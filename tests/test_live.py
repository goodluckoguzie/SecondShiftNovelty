import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ollama_client import ollama_available


@pytest.mark.live
def test_ollama_extracts_ravi_line():
    if not ollama_available():
        pytest.skip("Ollama is not running")
    with TestClient(app) as client:
        response = client.post(
            "/log",
            json={
                "transcript": "Gave dad his 8pm meds, 40 minutes late. More confused again this evening."
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["events"]
