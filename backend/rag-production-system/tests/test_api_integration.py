import os
from pathlib import Path
import pytest

# Ensure tests run with local ollama provider by default so no remote API key is required for route tests
os.environ["CHAT_PROVIDER"] = "ollama"

from fastapi.testclient import TestClient

from app.main import app
from app.api.jobs import job_manager
from app.evaluation.runner import parse_evaluation_report
from app.core.security import validate_session_id


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_system_info_endpoint(client: TestClient):
    response = client.get("/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "environment" in data
    assert "chat_provider" in data
    assert "parent_chunk_size" in data
    assert "rerank_top_n" in data
    # Ensure no secrets are leaked
    assert "api_key" not in str(data).lower()
    assert "groq_api_key" not in data
    assert "gemini_api_key" not in data


def test_chat_sessions_route_order(client: TestClient):
    """Explicitly verifies that GET /chat/sessions is NOT matched as /chat/{session_id}."""
    response = client.get("/chat/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_session_messages_empty(client: TestClient):
    response = client.get("/chat/test-nonexistent-session/messages")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-nonexistent-session"
    assert data["messages"] == []


def test_invalid_session_id_validation():
    # Direct validation test
    with pytest.raises(ValueError):
        validate_session_id("../../etc/passwd")
    with pytest.raises(ValueError):
        validate_session_id("invalid session with spaces")
    with pytest.raises(ValueError):
        validate_session_id("")


def test_invalid_session_id_endpoint(client: TestClient):
    # Invalid characters in path parameter
    response = client.get("/chat/invalid@session!id/messages")
    assert response.status_code == 400
    assert "Invalid session_id" in response.json()["detail"]


def test_documents_listing(client: TestClient):
    response = client.get("/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_evaluate_status_not_found(client: TestClient):
    response = client.get("/evaluate/non-existent-job-id")
    assert response.status_code == 404


def test_evaluate_results_not_completed(client: TestClient):
    # Create a dummy queued job
    import asyncio
    job = asyncio.run(job_manager.create())
    response = client.get(f"/evaluate/{job.job_id}/results")
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"].lower()


def test_parse_evaluation_report(tmp_path: Path):
    csv_file = tmp_path / "test_eval_report.csv"
    csv_file.write_text(
        "question,expected_output,actual_output,success,Faithfulness_score,Faithfulness_passed,Faithfulness_reason,Faithfulness_error,Answer Relevancy_score,Answer Relevancy_passed,Answer Relevancy_reason,Answer Relevancy_error\n"
        "What is X?,It is Y.,It is Y.,True,1.0,True,Grounded in context,,0.95,True,Relevant answer,\n"
        "What is Z?,It is W.,I do not know.,False,0.5,False,Missing fact,,0.4,False,Off topic,\n",
        encoding="utf-8"
    )
    result = parse_evaluation_report(csv_file, "job-123")
    assert result["job_id"] == "job-123"
    assert result["status"] == "completed"
    assert result["summary"]["total_cases"] == 2
    assert result["summary"]["passed_cases"] == 1
    assert result["summary"]["average_scores"]["Faithfulness"] == 0.75
    assert result["summary"]["average_scores"]["Answer Relevancy"] == 0.675
    assert len(result["test_cases"]) == 2
    assert result["test_cases"][0]["metrics"]["Faithfulness"]["score"] == 1.0
    assert result["test_cases"][0]["metrics"]["Faithfulness"]["passed"] is True
