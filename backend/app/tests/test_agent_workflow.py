import json
from collections.abc import Generator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def register_token(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Agent User", "email": email, "password": "strong-password"},
    )
    assert response.status_code == 201
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def collect_sse_events(response: Response) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    event_name = "message"
    data_lines: list[str] = []
    for line in response.iter_lines():
        if line == "":
            if data_lines:
                decoded = json.loads("\n".join(data_lines))
                events.append((event_name, cast(dict[str, Any], decoded)))
            event_name = "message"
            data_lines = []
            continue
        if line.startswith("event:"):
            event_name = line.replace("event:", "", 1).strip()
        elif line.startswith("data:"):
            data_lines.append(line.replace("data:", "", 1).strip())
    if data_lines:
        decoded = json.loads("\n".join(data_lines))
        events.append((event_name, cast(dict[str, Any], decoded)))
    return events


def prepare_agent_inputs(client: TestClient, token: str) -> None:
    headers = auth_headers(token)
    assert (
        client.put(
            "/api/v1/profile/me",
            headers=headers,
            json={
                "age": 25,
                "gender": "female",
                "height_cm": 165,
                "weight_kg": 58,
                "sleep_hours": 6,
                "bedtime": "01:00:00",
                "wake_time": "07:30:00",
                "activity_level": "sedentary",
                "exercise_frequency": 1,
                "dietary_preferences": ["canteen", "takeaway"],
                "allergies": [],
                "budget_level": "medium",
            },
        ).status_code
        == 200
    )
    assert (
        client.put(
            "/api/v1/fitness-profile/me",
            headers=headers,
            json={
                "exercise_level": "intermediate",
                "weekly_frequency": 2,
                "preferred_exercise": ["walking", "cycling", "strength"],
                "available_time_minutes": 45,
                "fitness_goal": "fat_loss",
                "contraindications": [],
                "is_sedentary": True,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/goals",
            headers=headers,
            json={
                "goal_type": "fat_loss",
                "target_weight_kg": 54,
                "target_calories": 1800,
                "target_protein_g": 90,
                "start_date": "2026-05-15",
                "status": "active",
            },
        ).status_code
        == 201
    )

    meal_payloads = [
        {
            "meal_date": "2026-05-15",
            "meal_time": "12:30:00",
            "meal_type": "lunch",
            "location": "takeaway",
            "food_items": [
                {
                    "name": "fried chicken burger set",
                    "amount": 1,
                    "unit": "set",
                    "calories": 1200,
                    "protein_g": 30,
                    "fat_g": 55,
                    "carbs_g": 95,
                    "fiber_g": 4,
                    "sugar_g": 20,
                    "sodium_mg": 1800,
                }
            ],
        },
        {
            "meal_date": "2026-05-15",
            "meal_time": "23:00:00",
            "meal_type": "night_snack",
            "location": "convenience_store",
            "food_items": [
                {
                    "name": "milk tea",
                    "amount": 1,
                    "unit": "cup",
                    "calories": 450,
                    "protein_g": 5,
                    "fat_g": 12,
                    "carbs_g": 80,
                    "fiber_g": 0,
                    "sugar_g": 58,
                    "sodium_mg": 180,
                }
            ],
        },
    ]
    for payload in meal_payloads:
        assert client.post("/api/v1/meals", headers=headers, json=payload).status_code == 201


def test_agent_chat_runs_graph_and_persists_trace(client: TestClient) -> None:
    token = register_token(client, "agent@example.com")
    headers = auth_headers(token)
    prepare_agent_inputs(client, token)

    response = client.post(
        "/api/v1/agent/chat",
        headers=headers,
        json={
            "message": "今天中午吃了炸鸡汉堡，晚上又喝了奶茶，我想减脂应该怎么调整？",
            "analysis_date": "2026-05-15",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["run"]["status"] == "completed"
    assert body["state"]["goal"] == "fat_loss"
    assert body["state"]["nutrition_analysis"]["score"] < 80
    assert len(body["state"]["risks"]) >= 4
    assert body["state"]["exercise_recommendation"]["recommended_plan"]
    assert "饮食分析闭环" in body["assistant_message"]["content"]

    session_id = body["session"]["id"]
    run_id = body["run"]["id"]

    messages_response = client.get(
        f"/api/v1/agent/sessions/{session_id}/messages",
        headers=headers,
    )
    assert messages_response.status_code == 200
    assert [message["role"] for message in messages_response.json()] == ["user", "assistant"]

    tool_calls_response = client.get(
        f"/api/v1/agent/runs/{run_id}/tool-calls",
        headers=headers,
    )
    assert tool_calls_response.status_code == 200
    tool_names = {item["tool_name"] for item in tool_calls_response.json()}
    assert {
        "planner_goal_inference",
        "profile_reader",
        "nutrition_calculator",
        "risk_evaluator",
        "meal_plan_generator",
        "exercise_plan_generator",
        "intervention_tracker",
    }.issubset(tool_names)


def test_agent_chat_stream_emits_progress_tool_calls_and_final_result(
    client: TestClient,
) -> None:
    token = register_token(client, "agent-stream@example.com")
    headers = auth_headers(token)
    prepare_agent_inputs(client, token)

    with client.stream(
        "POST",
        "/api/v1/agent/chat/stream",
        headers=headers,
        json={
            "message": "今天中午吃了炸鸡汉堡，晚上又喝了奶茶，我想减脂应该怎么调整？",
            "analysis_date": "2026-05-15",
        },
    ) as response:
        assert response.status_code == 200
        events = collect_sse_events(response)

    event_names = [name for name, _ in events]
    assert "session" in event_names
    assert event_names.count("node") >= 7
    assert "tool_call" in event_names
    assert "answer_delta" in event_names
    assert event_names[-1] == "final"

    final_payload = next(data for name, data in events if name == "final")
    result = cast(dict[str, Any], final_payload["result"])
    state = cast(dict[str, Any], result["state"])
    assert cast(dict[str, Any], result["run"])["status"] == "completed"
    assert state["goal"] == "fat_loss"
    assert cast(dict[str, Any], state["exercise_recommendation"])["recommended_plan"]


def test_agent_session_access_is_user_scoped(client: TestClient) -> None:
    owner_token = register_token(client, "agent-owner@example.com")
    other_token = register_token(client, "agent-other@example.com")

    session_response = client.post(
        "/api/v1/agent/sessions",
        headers=auth_headers(owner_token),
        json={"title": "Owner Session"},
    )
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    forbidden_response = client.get(
        f"/api/v1/agent/sessions/{session_id}",
        headers=auth_headers(other_token),
    )
    assert forbidden_response.status_code == 404
