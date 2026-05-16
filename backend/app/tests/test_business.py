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
        json={"name": "测试用户", "email": email, "password": "strong-password"},
    )
    assert response.status_code == 201
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_profile_fitness_goal_and_meal_flow(client: TestClient) -> None:
    token = register_token(client, "business@example.com")
    headers = auth_headers(token)

    profile_response = client.put(
        "/api/v1/profile/me",
        headers=headers,
        json={
            "age": 24,
            "gender": "female",
            "height_cm": 166,
            "weight_kg": 58,
            "sleep_hours": 6.5,
            "bedtime": "00:30:00",
            "wake_time": "07:30:00",
            "activity_level": "sedentary",
            "exercise_frequency": 2,
            "dietary_preferences": ["食堂", "少辣"],
            "allergies": [],
            "budget_level": "medium",
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["activity_level"] == "sedentary"
    assert client.get("/api/v1/profile/me", headers=headers).status_code == 200

    fitness_response = client.put(
        "/api/v1/fitness-profile/me",
        headers=headers,
        json={
            "exercise_level": "beginner",
            "weekly_frequency": 2,
            "preferred_exercise": ["快走", "自重训练"],
            "available_time_minutes": 45,
            "fitness_goal": "fat_loss",
            "contraindications": ["膝盖不适时避免跳跃"],
            "is_sedentary": True,
        },
    )
    assert fitness_response.status_code == 200
    assert fitness_response.json()["available_time_minutes"] == 45

    goal_response = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "goal_type": "fat_loss",
            "target_weight_kg": 55,
            "target_calories": 1800,
            "target_protein_g": 90,
            "start_date": "2026-05-15",
            "end_date": "2026-08-15",
            "status": "active",
        },
    )
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    status_response = client.patch(
        f"/api/v1/goals/{goal_id}/status",
        headers=headers,
        json={"status": "paused"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "paused"

    meal_response = client.post(
        "/api/v1/meals",
        headers=headers,
        json={
            "meal_date": "2026-05-15",
            "meal_time": "12:20:00",
            "meal_type": "lunch",
            "location": "食堂",
            "source": "manual",
            "note": "训练日前午餐",
            "food_items": [
                {
                    "name": "鸡胸肉饭",
                    "amount": 1,
                    "unit": "份",
                    "calories": 620,
                    "protein_g": 38,
                    "fat_g": 16,
                    "carbs_g": 82,
                    "fiber_g": 5,
                    "sugar_g": 4,
                    "sodium_mg": 850,
                }
            ],
        },
    )
    assert meal_response.status_code == 201
    meal_body = meal_response.json()
    meal_id = meal_body["id"]
    assert meal_body["food_items"][0]["name"] == "鸡胸肉饭"

    list_response = client.get(
        "/api/v1/meals?start_date=2026-05-15&end_date=2026-05-15",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(
        f"/api/v1/meals/{meal_id}",
        headers=headers,
        json={
            "note": "已更新",
            "food_items": [
                {
                    "name": "牛奶",
                    "amount": 250,
                    "unit": "ml",
                    "calories": 150,
                    "protein_g": 8,
                    "fat_g": 5,
                    "carbs_g": 12,
                    "fiber_g": 0,
                    "sugar_g": 12,
                    "sodium_mg": 120,
                }
            ],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["note"] == "已更新"
    assert update_response.json()["food_items"][0]["name"] == "牛奶"

    delete_response = client.delete(f"/api/v1/meals/{meal_id}", headers=headers)
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/meals/{meal_id}", headers=headers).status_code == 404


def test_meal_access_is_user_scoped(client: TestClient) -> None:
    owner_token = register_token(client, "owner@example.com")
    other_token = register_token(client, "other@example.com")

    meal_response = client.post(
        "/api/v1/meals",
        headers=auth_headers(owner_token),
        json={
            "meal_date": "2026-05-15",
            "meal_type": "dinner",
            "food_items": [],
        },
    )
    assert meal_response.status_code == 201
    meal_id = meal_response.json()["id"]

    forbidden_response = client.get(
        f"/api/v1/meals/{meal_id}",
        headers=auth_headers(other_token),
    )
    assert forbidden_response.status_code == 404
