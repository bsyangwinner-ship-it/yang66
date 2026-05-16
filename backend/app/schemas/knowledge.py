from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source: str = Field(default="manual", max_length=200)
    category: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class KnowledgeDocumentRead(BaseModel):
    id: str
    title: str
    source: str
    category: str
    content: str
    metadata: dict[str, object] = Field(validation_alias="document_metadata")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeChunkRead(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    token_count: int
    metadata: dict[str, object] = Field(validation_alias="chunk_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentWithChunks(KnowledgeDocumentRead):
    chunks: list[KnowledgeChunkRead]


class KnowledgeEmbedRequest(BaseModel):
    max_chars: int = Field(default=600, ge=200, le=2000)
    overlap_chars: int = Field(default=80, ge=0, le=400)


class KnowledgeEmbedResponse(BaseModel):
    document_id: str
    chunk_count: int
    embedding_provider: str


class KnowledgeSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    source: str
    category: str
    chunk_text: str
    similarity: float
    metadata: dict[str, object]


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResult]
