from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    goal_type: str | None = Field(default=None, max_length=48)


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    analysis_date: date | None = None
    title: str | None = Field(default=None, max_length=160)


class AgentMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    analysis_date: date | None = None


class AgentSessionRead(BaseModel):
    id: str
    user_id: str
    title: str
    goal_snapshot: dict[str, object]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentMessageRead(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    metadata: dict[str, object] = Field(validation_alias="message_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunRead(BaseModel):
    id: str
    session_id: str
    graph_name: str
    state: dict[str, object]
    status: str
    started_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AgentToolCallRead(BaseModel):
    id: str
    run_id: str
    tool_name: str
    input: dict[str, object]
    output: dict[str, object]
    status: str
    latency_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunResult(BaseModel):
    session: AgentSessionRead
    run: AgentRunRead
    assistant_message: AgentMessageRead
    state: dict[str, object]
