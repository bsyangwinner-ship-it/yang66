import re
from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from typing import Any, cast

from openai import OpenAI
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.knowledge import EMBEDDING_DIMENSIONS, KnowledgeChunk, KnowledgeDocument
from app.schemas.knowledge import KnowledgeDocumentCreate

CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]+")


@dataclass(frozen=True)
class EmbeddingOutput:
    embedding: list[float]
    provider: str


@dataclass(frozen=True)
class KnowledgeSearchItem:
    chunk_id: str
    document_id: str
    document_title: str
    source: str
    category: str
    chunk_text: str
    similarity: float
    metadata: dict[str, object]


def _resize_embedding(embedding: Sequence[float]) -> list[float]:
    resized = [float(value) for value in embedding[:EMBEDDING_DIMENSIONS]]
    if len(resized) < EMBEDDING_DIMENSIONS:
        resized.extend([0.0] * (EMBEDDING_DIMENSIONS - len(resized)))
    return resized


def _is_cjk(text: str) -> bool:
    return bool(CJK_PATTERN.fullmatch(text))


def tokenize_text(text: str) -> list[str]:
    tokens: list[str] = []
    for part in TOKEN_PATTERN.findall(text.lower()):
        if _is_cjk(part):
            tokens.extend(part)
            tokens.extend(part[index : index + 2] for index in range(max(len(part) - 1, 0)))
            if len(part) > 2:
                tokens.append(part)
        else:
            tokens.append(part)
    return [token for token in tokens if token.strip()]


def _local_hash_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    tokens = tokenize_text(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        vector[index] += 1.0

    norm = sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def generate_embedding(text: str) -> EmbeddingOutput:
    if settings.openai_api_key:
        try:
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text,
            )
            return EmbeddingOutput(
                embedding=_resize_embedding(response.data[0].embedding),
                provider="openai",
            )
        except Exception:
            if not settings.enable_rule_fallback:
                raise

    return EmbeddingOutput(embedding=_local_hash_embedding(text), provider="local_hash")


def chunk_text(content: str, max_chars: int = 600, overlap_chars: int = 80) -> list[str]:
    cleaned = re.sub(r"\s+", " ", content).strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    step = max(max_chars - overlap_chars, 1)
    start = 0
    while start < len(cleaned):
        chunk = cleaned[start : start + max_chars].strip()
        if chunk:
            chunks.append(chunk)
        if start + max_chars >= len(cleaned):
            break
        start += step
    return chunks


def create_knowledge_document(
    db: Session,
    payload: KnowledgeDocumentCreate,
) -> KnowledgeDocument:
    document = KnowledgeDocument(
        title=payload.title,
        source=payload.source,
        category=payload.category,
        content=payload.content,
        document_metadata=payload.metadata,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def embed_knowledge_document(
    db: Session,
    document: KnowledgeDocument,
    max_chars: int = 600,
    overlap_chars: int = 80,
) -> tuple[int, str]:
    chunks = chunk_text(document.content, max_chars=max_chars, overlap_chars=overlap_chars)
    db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))

    provider = "local_hash"
    for index, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)
        provider = embedding.provider
        db.add(
            KnowledgeChunk(
                document_id=document.id,
                chunk_index=index,
                chunk_text=chunk,
                token_count=len(tokenize_text(chunk)),
                embedding=embedding.embedding,
                chunk_metadata={
                    "embedding_provider": embedding.provider,
                    "embedding_model": settings.openai_embedding_model
                    if embedding.provider == "openai"
                    else "deterministic-hash",
                },
            )
        )

    db.commit()
    db.refresh(document)
    return len(chunks), provider


def _embedding_values(value: object) -> list[float]:
    if hasattr(value, "tolist"):
        return [float(item) for item in value.tolist()]
    return [float(item) for item in cast(Sequence[float], value)]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(length))
    left_norm = sqrt(sum(value * value for value in left[:length]))
    right_norm = sqrt(sum(value * value for value in right[:length]))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def search_knowledge(
    db: Session,
    query: str,
    top_k: int = 5,
    category: str | None = None,
    min_similarity: float = 0.0,
) -> list[KnowledgeSearchItem]:
    query_embedding = generate_embedding(query).embedding
    statement = select(KnowledgeChunk).options(selectinload(KnowledgeChunk.document))
    if category is not None:
        statement = statement.join(KnowledgeChunk.document).where(
            KnowledgeDocument.category == category
        )

    matches: list[KnowledgeSearchItem] = []
    for chunk in db.scalars(statement):
        similarity = cosine_similarity(query_embedding, _embedding_values(chunk.embedding))
        if similarity < min_similarity:
            continue
        document = chunk.document
        metadata: dict[str, object] = {
            **document.document_metadata,
            **chunk.chunk_metadata,
        }
        matches.append(
            KnowledgeSearchItem(
                chunk_id=chunk.id,
                document_id=document.id,
                document_title=document.title,
                source=document.source,
                category=document.category,
                chunk_text=chunk.chunk_text,
                similarity=round(similarity, 4),
                metadata=metadata,
            )
        )

    matches.sort(key=lambda item: item.similarity, reverse=True)
    return matches[:top_k]


def search_knowledge_context(
    db: Session,
    query: str,
    top_k: int = 3,
    category: str | None = None,
) -> list[dict[str, Any]]:
    return [
        {
            "document_id": item.document_id,
            "title": item.document_title,
            "source": item.source,
            "category": item.category,
            "excerpt": item.chunk_text,
            "similarity": item.similarity,
        }
        for item in search_knowledge(db, query=query, top_k=top_k, category=category)
    ]
