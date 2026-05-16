from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    KnowledgeDocumentWithChunks,
    KnowledgeEmbedRequest,
    KnowledgeEmbedResponse,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)
from app.services.knowledge import (
    create_knowledge_document,
    embed_knowledge_document,
    search_knowledge,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def get_document(db: Session, document_id: str) -> KnowledgeDocument:
    document = db.scalar(
        select(KnowledgeDocument)
        .options(selectinload(KnowledgeDocument.chunks))
        .where(KnowledgeDocument.id == document_id)
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )
    return document


@router.get("/documents", response_model=list[KnowledgeDocumentRead])
def list_documents(
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    category: str | None = None,
) -> list[KnowledgeDocument]:
    statement = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    if category is not None:
        statement = statement.where(KnowledgeDocument.category == category)
    return list(db.scalars(statement))


@router.post(
    "/documents",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    payload: KnowledgeDocumentCreate,
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeDocument:
    return create_knowledge_document(db, payload)


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentWithChunks)
def read_document(
    document_id: str,
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeDocument:
    return get_document(db, document_id)


@router.post("/documents/{document_id}/embed", response_model=KnowledgeEmbedResponse)
def embed_document(
    document_id: str,
    payload: KnowledgeEmbedRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeEmbedResponse:
    document = get_document(db, document_id)
    chunk_count, provider = embed_knowledge_document(
        db,
        document,
        max_chars=payload.max_chars,
        overlap_chars=payload.overlap_chars,
    )
    return KnowledgeEmbedResponse(
        document_id=document.id,
        chunk_count=chunk_count,
        embedding_provider=provider,
    )


@router.get("/search", response_model=KnowledgeSearchResponse)
def search_documents(
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(min_length=1)],
    top_k: Annotated[int, Query(ge=1, le=20)] = 5,
    category: str | None = None,
) -> KnowledgeSearchResponse:
    results = [
        KnowledgeSearchResult(
            chunk_id=item.chunk_id,
            document_id=item.document_id,
            document_title=item.document_title,
            source=item.source,
            category=item.category,
            chunk_text=item.chunk_text,
            similarity=item.similarity,
            metadata=item.metadata,
        )
        for item in search_knowledge(db, query=q, top_k=top_k, category=category)
    ]
    return KnowledgeSearchResponse(query=q, results=results)
