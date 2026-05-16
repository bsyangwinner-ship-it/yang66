import json
from collections.abc import Generator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.agent import AgentMessage, AgentRun, AgentSession, AgentToolCall
from app.models.auth import User
from app.schemas.agent import (
    AgentChatRequest,
    AgentMessageCreate,
    AgentMessageRead,
    AgentRunRead,
    AgentRunResult,
    AgentSessionCreate,
    AgentSessionRead,
    AgentToolCallRead,
)
from app.services.agent_runner import (
    create_agent_session,
    create_chat_session,
    run_agent_for_message,
    stream_agent_for_message,
)

router = APIRouter(prefix="/agent", tags=["agent"])


def _sse_event(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def get_owned_session(db: Session, user_id: str, session_id: str) -> AgentSession:
    session = db.get(AgentSession, session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent session not found")
    return session


def get_owned_run(db: Session, user_id: str, run_id: str) -> AgentRun:
    run = db.scalar(
        select(AgentRun)
        .options(selectinload(AgentRun.session))
        .where(AgentRun.id == run_id)
    )
    if run is None or run.session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return run


@router.get("/capabilities")
def get_agent_capabilities() -> dict[str, list[str]]:
    return {
        "agents": [
            "planner",
            "profile_interpreter",
            "nutrition_analyzer",
            "risk_detector",
            "knowledge_retriever",
            "meal_plan_recommender",
            "exercise_intervention_recommender",
            "intervention_tracker",
        ],
        "tools": [
            "planner_goal_inference",
            "profile_reader",
            "meal_history_reader",
            "nutrition_calculator",
            "risk_evaluator",
            "rag_search",
            "meal_plan_generator",
            "calorie_surplus_calculator",
            "activity_energy_cost_estimator",
            "fitness_profile_reader",
            "recent_diet_trend_reader",
            "exercise_plan_generator",
            "intervention_tracker",
        ],
    }


@router.get("/sessions", response_model=list[AgentSessionRead])
def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AgentSession]:
    return list(
        db.scalars(
            select(AgentSession)
            .where(AgentSession.user_id == current_user.id)
            .order_by(AgentSession.updated_at.desc())
        )
    )


@router.post("/sessions", response_model=AgentSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: AgentSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentSession:
    return create_agent_session(db, current_user.id, payload)


@router.get("/sessions/{session_id}", response_model=AgentSessionRead)
def get_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentSession:
    return get_owned_session(db, current_user.id, session_id)


@router.get("/sessions/{session_id}/messages", response_model=list[AgentMessageRead])
def list_messages(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AgentMessage]:
    session = get_owned_session(db, current_user.id, session_id)
    return list(
        db.scalars(
            select(AgentMessage)
            .where(AgentMessage.session_id == session.id)
            .order_by(AgentMessage.created_at)
        )
    )


@router.post("/sessions/{session_id}/messages", response_model=AgentRunResult)
def send_message(
    session_id: str,
    payload: AgentMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentRunResult:
    session = get_owned_session(db, current_user.id, session_id)
    run, assistant_message, state = run_agent_for_message(
        db,
        session,
        payload.content,
        payload.analysis_date,
    )
    return AgentRunResult(
        session=AgentSessionRead.model_validate(session),
        run=AgentRunRead.model_validate(run),
        assistant_message=AgentMessageRead.model_validate(assistant_message),
        state=state,
    )


@router.post("/chat", response_model=AgentRunResult, status_code=status.HTTP_201_CREATED)
def chat(
    payload: AgentChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentRunResult:
    session = create_chat_session(db, current_user.id, payload)
    run, assistant_message, state = run_agent_for_message(
        db,
        session,
        payload.message,
        payload.analysis_date,
    )
    return AgentRunResult(
        session=AgentSessionRead.model_validate(session),
        run=AgentRunRead.model_validate(run),
        assistant_message=AgentMessageRead.model_validate(assistant_message),
        state=state,
    )


@router.post("/chat/stream")
def chat_stream(
    payload: AgentChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    session = create_chat_session(db, current_user.id, payload)

    def event_stream() -> Generator[str, None, None]:
        for item in stream_agent_for_message(
            db,
            session,
            payload.message,
            payload.analysis_date,
        ):
            yield _sse_event(str(item["event"]), dict(item["data"]))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/runs/{run_id}", response_model=AgentRunRead)
def get_run(
    run_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentRun:
    return get_owned_run(db, current_user.id, run_id)


@router.get("/runs/{run_id}/tool-calls", response_model=list[AgentToolCallRead])
def list_tool_calls(
    run_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AgentToolCall]:
    run = get_owned_run(db, current_user.id, run_id)
    return list(
        db.scalars(
            select(AgentToolCall)
            .where(AgentToolCall.run_id == run.id)
            .order_by(AgentToolCall.created_at)
        )
    )
