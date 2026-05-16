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
        json={"name": "Report User", "email": email, "password": "strong-password"},
    )
    assert response.status_code == 201
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def prepare_report_inputs(client: TestClient, headers: dict[str, str]) -> None:
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
        client.post(
            "/api/v1/goals",
            headers=headers,
            json={
                "goal_type": "fat_loss",
                "target_weight_kg": 58,
                "target_calories": 1700,
                "target_protein_g": 90,
                "start_date": "2026-05-10",
                "status": "active",
            },
        ).status_code
        == 201
    )

    meal_payloads = [
        {
            "meal_date": "2026-05-10",
            "meal_time": "12:30:00",
            "meal_type": "lunch",
            "location": "takeaway",
            "food_items": [
                {
                    "name": "fried chicken burger",
                    "amount": 1,
                    "unit": "serving",
                    "calories": 760,
                    "protein_g": 24,
                    "fat_g": 42,
                    "carbs_g": 70,
                    "fiber_g": 3,
                    "sugar_g": 8,
                    "sodium_mg": 1400,
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
        {
            "meal_date": "2026-05-11",
            "meal_time": "20:10:00",
            "meal_type": "dinner",
            "location": "canteen",
            "food_items": [
                {
                    "name": "chicken rice",
                    "amount": 1,
                    "unit": "serving",
                    "calories": 680,
                    "protein_g": 35,
                    "fat_g": 18,
                    "carbs_g": 88,
                    "fiber_g": 5,
                    "sugar_g": 6,
                    "sodium_mg": 900,
                }
            ],
        },
    ]
    for payload in meal_payloads:
        assert client.post("/api/v1/meals", headers=headers, json=payload).status_code == 201


def test_generate_report_and_intervention_flow(client: TestClient) -> None:
    token = register_token(client, "report@example.com")
    headers = auth_headers(token)
    prepare_report_inputs(client, headers)

    response = client.post(
        "/api/v1/reports/generate",
        headers=headers,
        json={
            "report_type": "weekly",
            "period_start": "2026-05-10",
            "period_end": "2026-05-16",
            "run_async": False,
        },
    )

    assert response.status_code == 201
    body = response.json()
    report = body["report"]
    assert report["status"] == "completed"
    assert report["metrics"]["analysis_count"] == 2
    assert report["recommendations"]
    assert report["export_object_key"].endswith(".md")
    assert "健康建议仅作辅助参考" in report["export_content"]
    assert body["intervention_count"] >= 1

    list_response = client.get("/api/v1/reports", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    interventions_response = client.get("/api/v1/interventions?task_status=open", headers=headers)
    assert interventions_response.status_code == 200
    interventions = interventions_response.json()
    assert interventions

    task_id = interventions[0]["id"]
    status_response = client.patch(
        f"/api/v1/interventions/{task_id}/status",
        headers=headers,
        json={"status": "completed"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"
    assert status_response.json()["completed_at"] is not None


def test_report_access_is_user_scoped(client: TestClient) -> None:
    owner_token = register_token(client, "report-owner@example.com")
    other_token = register_token(client, "report-other@example.com")
    owner_headers = auth_headers(owner_token)
    prepare_report_inputs(client, owner_headers)

    response = client.post(
        "/api/v1/reports/generate",
        headers=owner_headers,
        json={
            "report_type": "weekly",
            "period_start": "2026-05-10",
            "period_end": "2026-05-16",
        },
    )
    assert response.status_code == 201
    report_id = response.json()["report"]["id"]

    forbidden_response = client.get(
        f"/api/v1/reports/{report_id}",
        headers=auth_headers(other_token),
    )
    assert forbidden_response.status_code == 404
