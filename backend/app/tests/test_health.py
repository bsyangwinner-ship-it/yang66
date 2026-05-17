from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_localhost_and_loopback_frontend_origins_are_allowed() -> None:
    client = TestClient(create_app())

    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_agent_capabilities() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/agent/capabilities")

    assert response.status_code == 200
    assert "planner" in response.json()["agents"]
    assert "exercise_intervention_recommender" in response.json()["agents"]
    assert "exercise_plan_generator" in response.json()["tools"]


def test_prometheus_metrics_endpoint_records_requests() -> None:
    client = TestClient(create_app())

    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "nutrition_agent_app_info" in response.text
    assert "nutrition_agent_http_requests_total" in response.text
    assert 'path="/health"' in response.text
