from collections.abc import Generator
from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy.orm import Session

from app.agents.graph import GRAPH_NAME, run_nutrition_agent, stream_nutrition_agent
from app.models.agent import AgentMessage, AgentRun, AgentSession, AgentToolCall
from app.schemas.agent import (
    AgentChatRequest,
    AgentMessageRead,
    AgentRunRead,
    AgentRunResult,
    AgentSessionCreate,
    AgentSessionRead,
)

NODE_LABELS = {
    "planner": "目标理解",
    "profile": "读取画像",
    "nutrition": "营养分析",
    "risk": "风险识别",
    "knowledge": "RAG 检索",
    "meal_plan": "餐单推荐",
    "exercise": "运动干预",
    "intervention": "长期追踪",
}


def _today() -> date:
    return datetime.now(UTC).date()


def _session_title(title: str | None, message: str | None = None) -> str:
    if title:
        return title
    if message:
        cleaned = " ".join(message.split())
        return cleaned[:48] or "新的饮食咨询"
    return "新的饮食咨询"


def create_agent_session(
    db: Session,
    user_id: str,
    payload: AgentSessionCreate,
) -> AgentSession:
    session = AgentSession(
        user_id=user_id,
        title=_session_title(payload.title),
        goal_snapshot={"goal_type": payload.goal_type} if payload.goal_type else {},
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_chat_session(
    db: Session,
    user_id: str,
    payload: AgentChatRequest,
) -> AgentSession:
    session = AgentSession(
        user_id=user_id,
        title=_session_title(payload.title, payload.message),
        goal_snapshot={},
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _create_run_shell(
    db: Session,
    session: AgentSession,
    content: str,
    analysis_date: date | None,
) -> tuple[AgentMessage, AgentRun, date]:
    selected_date = analysis_date or _today()
    user_message = AgentMessage(
        session_id=session.id,
        role="user",
        content=content,
        message_metadata={"analysis_date": selected_date.isoformat()},
    )
    run = AgentRun(
        session_id=session.id,
        graph_name=GRAPH_NAME,
        status="running",
        state={},
    )
    db.add_all([user_message, run])
    db.flush()
    return user_message, run, selected_date


def _persist_successful_run(
    db: Session,
    session: AgentSession,
    run: AgentRun,
    state: dict[str, Any],
) -> tuple[AgentRun, AgentMessage, dict[str, Any]]:
    state_payload = cast(dict[str, object], state)
    run.state = state_payload
    run.status = "completed"
    run.finished_at = datetime.now(UTC)
    session.status = "active"
    session.goal_snapshot = {
        "goal": state.get("goal"),
        "analysis_date": state.get("analysis_date"),
        "risk_count": len(state.get("risks", [])),
    }

    for call in state.get("tool_calls", []):
        db.add(
            AgentToolCall(
                run_id=run.id,
                tool_name=str(call.get("tool_name", "unknown")),
                input=dict(call.get("input", {})),
                output=dict(call.get("output", {})),
                status=str(call.get("status", "success")),
                latency_ms=int(call.get("latency_ms", 0)),
            )
        )

    assistant_message = AgentMessage(
        session_id=session.id,
        role="assistant",
        content=str(state.get("final_response", "")),
        message_metadata={"run_id": run.id, "graph_name": GRAPH_NAME},
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(run)
    db.refresh(assistant_message)
    db.refresh(session)
    return run, assistant_message, state


def _run_result_payload(
    session: AgentSession,
    run: AgentRun,
    assistant_message: AgentMessage,
    state: dict[str, Any],
) -> dict[str, Any]:
    return AgentRunResult(
        session=AgentSessionRead.model_validate(session),
        run=AgentRunRead.model_validate(run),
        assistant_message=AgentMessageRead.model_validate(assistant_message),
        state=state,
    ).model_dump(mode="json")


def _state_preview(node: str, state: dict[str, Any]) -> dict[str, Any]:
    analysis = cast(dict[str, Any], state.get("nutrition_analysis", {}))
    totals = cast(dict[str, Any], analysis.get("totals", {}))
    meal_plan = cast(dict[str, Any], state.get("meal_plan", {}))
    exercise = cast(dict[str, Any], state.get("exercise_recommendation", {}))
    intervention = cast(dict[str, Any], state.get("intervention_plan", {}))
    if node == "planner":
        return {"goal": state.get("goal")}
    if node == "profile":
        return {
            "profile_complete": cast(dict[str, Any], state.get("profile_summary", {})).get(
                "complete"
            ),
            "fitness_level": cast(dict[str, Any], state.get("fitness_profile", {})).get(
                "exercise_level"
            ),
        }
    if node == "nutrition":
        return {
            "score": analysis.get("score"),
            "calories": totals.get("calories"),
            "protein_g": totals.get("protein_g"),
        }
    if node == "risk":
        return {"risk_count": len(state.get("risks", []))}
    if node == "knowledge":
        return {"rag_count": len(state.get("rag_context", []))}
    if node == "meal_plan":
        return {"today_adjustment_count": len(meal_plan.get("today_adjustment", []))}
    if node == "exercise":
        return {"exercise_count": len(exercise.get("recommended_plan", []))}
    if node == "intervention":
        return {"next_action_count": len(intervention.get("next_actions", []))}
    return {}


def _answer_chunks(content: str, size: int = 26) -> Generator[str, None, None]:
    for start in range(0, len(content), size):
        yield content[start : start + size]


def run_agent_for_message(
    db: Session,
    session: AgentSession,
    content: str,
    analysis_date: date | None,
) -> tuple[AgentRun, AgentMessage, dict[str, Any]]:
    _, run, selected_date = _create_run_shell(db, session, content, analysis_date)

    try:
        state = run_nutrition_agent(
            db=db,
            user_id=session.user_id,
            session_id=session.id,
            user_message=content,
            analysis_date=selected_date,
        )
        return _persist_successful_run(db, session, run, cast(dict[str, Any], state))
    except Exception:
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        db.commit()
        raise


def stream_agent_for_message(
    db: Session,
    session: AgentSession,
    content: str,
    analysis_date: date | None,
) -> Generator[dict[str, Any], None, None]:
    _, run, selected_date = _create_run_shell(db, session, content, analysis_date)
    user_id = session.user_id
    session_id = session.id
    db.commit()
    db.refresh(session)
    db.refresh(run)
    yield {
        "event": "session",
        "data": {
            "session": AgentSessionRead.model_validate(session).model_dump(mode="json"),
            "run": AgentRunRead.model_validate(run).model_dump(mode="json"),
        },
    }

    final_state: dict[str, Any] = {}
    emitted_tool_count = 0
    try:
        for step in stream_nutrition_agent(
            db=db,
            user_id=user_id,
            session_id=session_id,
            user_message=content,
            analysis_date=selected_date,
        ):
            node = str(step["node"])
            final_state = cast(dict[str, Any], step["state"])
            yield {
                "event": "node",
                "data": {
                    "node": node,
                    "label": NODE_LABELS.get(node, node),
                    "preview": _state_preview(node, final_state),
                },
            }

            tool_calls = cast(list[dict[str, Any]], final_state.get("tool_calls", []))
            for tool_call in tool_calls[emitted_tool_count:]:
                yield {"event": "tool_call", "data": {"tool_call": tool_call}}
            emitted_tool_count = len(tool_calls)

        run, assistant_message, state = _persist_successful_run(db, session, run, final_state)
        for chunk in _answer_chunks(assistant_message.content):
            yield {"event": "answer_delta", "data": {"content": chunk}}
        yield {
            "event": "final",
            "data": {"result": _run_result_payload(session, run, assistant_message, state)},
        }
    except Exception as exc:
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        db.commit()
        yield {"event": "error", "data": {"detail": str(exc)}}
