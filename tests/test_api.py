import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ExecuteResponse

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "Code Execution Service"


@patch("app.main.check_docker_available", new_callable=AsyncMock)
def test_health_check_healthy(mock_check):
    mock_check.return_value = True
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dockerAvailable"] is True
    assert "python" in data["supportedLanguages"]


@patch("app.main.check_docker_available", new_callable=AsyncMock)
def test_health_check_degraded(mock_check):
    mock_check.return_value = False
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dockerAvailable"] is False


@patch("app.main.run_code_in_sandbox", new_callable=AsyncMock)
def test_execute_endpoint_success(mock_run):
    mock_run.return_value = ExecuteResponse(
        jobId="test-job-123",
        stdout="Hello World\n",
        stderr="",
        exitCode=0,
        executionTimeMs=120,
        timestamp="2026-09-24T10:00:00Z",
    )

    payload = {
        "language": "python",
        "code": "print('Hello World')",
    }
    response = client.post("/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["jobId"] == "test-job-123"
    assert data["stdout"] == "Hello World\n"
    assert data["exitCode"] == 0


def test_execute_endpoint_validation_error():
    payload = {
        "language": "unsupported_lang",
        "code": "test",
    }
    response = client.post("/execute", json=payload)
    assert response.status_code == 422
