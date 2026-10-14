import os
import sys
from unittest.mock import patch

os.environ["DATABASE_PATH"] = "./test_entries.db"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import AIOutput

client = TestClient(app)


def teardown_module(module):
    if os.path.exists("./test_entries.db"):
        os.remove("./test_entries.db")


def test_reject_empty_input():
    response = client.post("/entries", json={"text": "   "})
    assert response.status_code == 422


def test_reject_missing_text():
    response = client.post("/entries", json={})
    assert response.status_code == 422


@patch("app.main.generate_summary_and_tags")
def test_create_and_list_entry(mock_generate):
    mock_generate.return_value = AIOutput(
        summary="A short summary.", tags=["tag-one", "tag-two", "tag-three"]
    )

    create_response = client.post("/entries", json={"text": "Some meeting notes about Q3 revenue."})
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["summary"] == "A short summary."
    assert body["tags"] == ["tag-one", "tag-two", "tag-three"]
    assert body["status"] == "completed"

    list_response = client.get("/entries")
    assert list_response.status_code == 200
    assert any(e["id"] == body["id"] for e in list_response.json())

    detail_response = client.get(f"/entries/{body['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["original_text"] == "Some meeting notes about Q3 revenue."


@patch("app.main.generate_summary_and_tags")
def test_ai_failure_persists_failed_entry(mock_generate):
    from app.llm import AIGenerationError

    mock_generate.side_effect = AIGenerationError("The AI service returned an error. Please try again.")

    response = client.post("/entries", json={"text": "Some text that will fail AI processing."})
    assert response.status_code == 502

    entries = client.get("/entries").json()
    assert any(e["status"] == "failed" for e in entries)
