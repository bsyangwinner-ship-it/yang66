from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
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
        json={"name": "RAG User", "email": email, "password": "strong-password"},
    )
    assert response.status_code == 201
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_and_embed_knowledge(
    client: TestClient,
    headers: dict[str, str],
    title: str = "Milk tea sugar intervention",
) -> str:
    document_response = client.post(
        "/api/v1/knowledge/documents",
        headers=headers,
        json={
            "title": title,
            "source": "local nutrition guide",
            "category": "risk_rule",
            "content": (
                "Milk tea and sweetened beverages can raise added sugar intake quickly. "
                "For fat loss, prefer unsweetened tea or water and pair the next meal "
                "with lean protein, vegetables, and a controlled staple portion."
            ),
            "metadata": {"version": "test"},
        },
    )
    assert document_response.status_code == 201
    document_id = document_response.json()["id"]

    embed_response = client.post(
        f"/api/v1/knowledge/documents/{document_id}/embed",
        headers=headers,
        json={"max_chars": 240, "overlap_chars": 20},
    )
    assert embed_response.status_code == 200
    assert embed_response.json()["chunk_count"] >= 1
    assert embed_response.json()["embedding_provider"] == "local_hash"
    return str(document_id)


def prepare_agent_inputs(client: TestClient, headers: dict[str, str]) -> None:
    assert (
        client.put(
            "/api/v1/profile/me",
            headers=headers,
            json={
                "age": 25,
                "gender": "female",
                "height_cm": 165,
                "weight_kg": 62,
                "sleep_hours": 6,
                "bedtime": "00:30:00",
                "wake_time": "07:30:00",
                "activity_level": "sedentary",
                "exercise_frequency": 1,
                "dietary_preferences": ["takeaway"],
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
                "exercise_level": "beginner",
                "weekly_frequency": 1,
                "preferred_exercise": ["walking"],
                "available_time_minutes": 35,
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
                "target_weight_kg": 58,
                "target_calories": 1750,
                "target_protein_g": 85,
                "start_date": "2026-05-16",
                "status": "active",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/meals",
            headers=headers,
            json={
                "meal_date": "2026-05-16",
                "meal_time": "21:30:00",
                "meal_type": "dinner",
                "location": "takeaway",
                "source": "manual",
                "note": "burger and milk tea",
                "food_items": [
                    {
                        "name": "fried chicken burger",
                        "amount": 1,
                        "unit": "serving",
                        "calories": 720,
                        "protein_g": 28,
                        "fat_g": 38,
                        "carbs_g": 66,
                        "fiber_g": 3,
                        "sugar_g": 8,
                        "sodium_mg": 1300,
                    },
                    {
                        "name": "milk tea",
                        "amount": 1,
                        "unit": "cup",
                        "calories": 420,
                        "protein_g": 4,
                        "fat_g": 12,
                        "carbs_g": 72,
                        "fiber_g": 0,
                        "sugar_g": 55,
                        "sodium_mg": 160,
                    },
                ],
            },
        ).status_code
        == 201
    )


def test_knowledge_document_embedding_and_search(client: TestClient) -> None:
    token = register_token(client, "knowledge@example.com")
    headers = auth_headers(token)
    document_id = create_and_embed_knowledge(client, headers)

    document_response = client.get(f"/api/v1/knowledge/documents/{document_id}", headers=headers)
    assert document_response.status_code == 200
    assert document_response.json()["chunks"]

    search_response = client.get(
        "/api/v1/knowledge/search?q=milk%20tea%20added%20sugar&top_k=1",
        headers=headers,
    )
    assert search_response.status_code == 200
    body = search_response.json()
    assert body["results"][0]["document_title"] == "Milk tea sugar intervention"
    assert body["results"][0]["similarity"] > 0


def test_agent_uses_rag_context(client: TestClient) -> None:
    token = register_token(client, "agent-rag@example.com")
    headers = auth_headers(token)
    prepare_agent_inputs(client, headers)
    create_and_embed_knowledge(client, headers)

    response = client.post(
        "/api/v1/agent/chat",
        headers=headers,
        json={
            "message": "I drank milk tea and want fat loss adjustment. What should I do?",
            "analysis_date": "2026-05-16",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["run"]["status"] == "completed"
    assert body["state"]["rag_context"]
    assert body["state"]["rag_context"][0]["title"] == "Milk tea sugar intervention"
    assert "Milk tea sugar intervention" in body["assistant_message"]["content"]

    tool_calls_response = client.get(
        f"/api/v1/agent/runs/{body['run']['id']}/tool-calls",
        headers=headers,
    )
    assert tool_calls_response.status_code == 200
    tool_names = {item["tool_name"] for item in tool_calls_response.json()}
    assert "rag_search" in tool_names
