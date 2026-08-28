from datetime import datetime


def test_ask_reads_notes_via_ollama(client, monkeypatch):
    monkeypatch.setattr("app.person_view.ollama_available", lambda: True)

    def fake_chat(prompt, system, timeout=90.0):
        assert "Question:" in prompt
        assert "Stored notes:" in prompt
        assert "Python already counted" in prompt
        return {"answer": "Confusion was logged in the evening.", "cite_ids": [], "in_notes": True}

    monkeypatch.setattr("app.person_view.chat_json", fake_chat)
    people = client.get("/people").json()
    dou = next(p for p in people if p["name"] == "Dou")
    response = client.post("/person/ask", json={"question": "Was he confused last night?", "person_id": dou["id"]})
    assert response.status_code == 200
    body = response.json()
    assert "confusion" in body["answer"].lower()
    assert "not a diagnosis" in body["disclaimer"].lower()


def test_ask_no_meal_today_asks_to_confirm(client, monkeypatch):
    class Frozen(datetime):
        @classmethod
        def utcnow(cls):
            return datetime(2026, 12, 25, 12, 0, 0)

    monkeypatch.setattr("app.person_view.datetime", Frozen)
    people = client.get("/people").json()
    dou = next(p for p in people if p["name"] == "Dou")
    response = client.post("/person/ask", json={"question": "has he eaten today", "person_id": dou["id"]})
    assert response.status_code == 200
    body = response.json()
    text = body["answer"].lower()
    assert "has not eaten" in text
    assert "confirm" in text
    assert "not in the notes" not in text or "do not show a meal" in text


def test_ask_meal_today_uses_record(client):
    people = client.get("/people").json()
    dou = next(p for p in people if p["name"] == "Dou")
    response = client.post("/person/ask", json={"question": "has he eaten today", "person_id": dou["id"]})
    assert response.status_code == 200
    text = response.json()["answer"].lower()
    assert "not in the notes" not in text
    assert "eaten" in text or "meal" in text or "supper" in text


def test_ask_needs_ollama(client, monkeypatch):
    monkeypatch.setattr("app.person_view.ollama_available", lambda: False)
    response = client.post("/person/ask", json={"question": "Was he confused?"})
    assert response.status_code == 503
