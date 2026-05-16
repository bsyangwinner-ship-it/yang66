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
        json={"name": "Analysis User", "email": email, "password": "strong-password"},
    )
    assert response.status_code == 201
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def prepare_analysis_inputs(client: TestClient, token: str) -> None:
    headers = auth_headers(token)
    profile_response = client.put(
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
    )
    assert profile_response.status_code == 200

    goal_response = client.post(
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
    )
    assert goal_response.status_code == 201

    for payload in [
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
            "meal_time": "21:30:00",
            "meal_type": "dinner",
            "location": "canteen",
            "food_items": [
                {
                    "name": "fried rice",
                    "amount": 1,
                    "unit": "bowl",
                    "calories": 850,
                    "protein_g": 18,
                    "fat_g": 35,
                    "carbs_g": 115,
                    "fiber_g": 3,
                    "sugar_g": 8,
                    "sodium_mg": 1300,
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
    ]:
        meal_response = client.post("/api/v1/meals", headers=headers, json=payload)
        assert meal_response.status_code == 201


def test_daily_analysis_generates_score_totals_and_risks(client: TestClient) -> None:
    token = register_token(client, "analysis@example.com")
    headers = auth_headers(token)
    prepare_analysis_inputs(client, token)

    response = client.post(
        "/api/v1/analysis/daily",
        headers=headers,
        json={"analysis_date": "2026-05-15"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score"] < 70
    assert body["totals"]["calories"] == 2500
    assert body["evidence"]["target_calories"] == 1800
    assert body["evidence"]["risk_count"] >= 6

    list_response = client.get(
        "/api/v1/analysis/daily?start_date=2026-05-15&end_date=2026-05-15",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    summary_response = client.get("/api/v1/analysis/summary", headers=headers)
    assert summary_response.status_code == 200
    assert summary_response.json()["count"] == 1


def test_risk_evaluation_status_update_and_user_scope(client: TestClient) -> None:
    owner_token = register_token(client, "risk-owner@example.com")
    other_token = register_token(client, "risk-other@example.com")
    owner_headers = auth_headers(owner_token)
    prepare_analysis_inputs(client, owner_token)

    evaluate_response = client.post(
        "/api/v1/risks/evaluate",
        headers=owner_headers,
        json={"analysis_date": "2026-05-15"},
    )
    assert evaluate_response.status_code == 200
    risks = evaluate_response.json()
    risk_types = {risk["risk_type"] for risk in risks}
    assert {
        "calorie_excess",
        "protein_low",
        "fiber_low",
        "sugar_high",
        "sodium_high",
        "breakfast_missing",
        "night_snack_frequent",
        "late_dinner",
    }.issubset(risk_types)

    risk_id = risks[0]["id"]
    update_response = client.patch(
        f"/api/v1/risks/{risk_id}/status",
        headers=owner_headers,
        json={"status": "resolved"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "resolved"
    assert update_response.json()["resolved_at"] is not None

    owner_list_response = client.get("/api/v1/risks?risk_status=resolved", headers=owner_headers)
    assert owner_list_response.status_code == 200
    assert len(owner_list_response.json()) == 1

    forbidden_response = client.patch(
        f"/api/v1/risks/{risk_id}/status",
        headers=auth_headers(other_token),
        json={"status": "resolved"},
    )
    assert forbidden_response.status_code == 404
