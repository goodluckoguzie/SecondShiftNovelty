def test_emergency_skips_ai(client, monkeypatch):
    called = {"ollama": False}

    def boom(*_args, **_kwargs):
        called["ollama"] = True
        raise AssertionError("Ollama must not run on emergency text")

    monkeypatch.setattr("app.main.ollama_extract", boom)
    response = client.post("/log", json={"transcript": "He is unconscious on the floor"})
    assert response.status_code == 200
    body = response.json()
    assert body["emergency"] is True
    assert "999" in body["screen"]
    assert body["events"] == []
    assert called["ollama"] is False


def test_handover_covers_72_hours(client):
    response = client.post("/handover", json={"name": "Priya"})
    assert response.status_code == 200
    markdown = response.json()["markdown"]
    assert "Priya" in markdown
    assert "72 hours" in markdown.lower() or "Last 72" in markdown
    pdf = client.get("/handover/latest.pdf")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"


def test_chart_includes_dose_change(client):
    data = client.get("/patterns").json()
    assert data["days"]
    assert data["dose_change"]
    assert data["dose_change"].startswith("2026-08-07")
