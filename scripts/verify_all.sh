#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is required"
  exit 1
fi

# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate secondshift
export PYTHONPATH="$ROOT/backend"

echo "== unit tests =="
python -m pytest tests/ -m "not live" -q

echo "== closed-loop smoke (text path) =="
python - <<'PY'
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.db import engine, init_db
from app.seed import seed_if_empty
from app.patterns import recompute_flags

init_db()
with Session(engine) as session:
    seed_if_empty(session)
    recompute_flags(session)

with TestClient(app) as client:
    assert client.get("/health").status_code == 200
    ravi = "Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week."
    logged = client.post("/log", json={"transcript": ravi, "use_heuristic": True})
    assert logged.status_code == 200, logged.text
    body = logged.json()
    assert body["emergency"] is False
    flags = body["flags"]
    assert any(f["kind"] == "symptom_recurrence" for f in flags), flags
    brief = client.post("/briefs")
    assert brief.status_code == 200
    assert "[log " in brief.json()["markdown"]
    pdf = client.get("/briefs/latest.pdf")
    assert pdf.content[:4] == b"%PDF"
    handover = client.post("/handover", json={"name": "your sister", "window": "72h"})
    assert handover.status_code == 200
    hp = client.get("/handover/latest.pdf")
    assert hp.content[:4] == b"%PDF"
    people = client.get("/people").json()
    able = next(p["id"] for p in people if p["name"] == "Able")
    able_line = "Able has eaten; after eating he was vomiting."
    logged_able = client.post("/log", json={"transcript": able_line, "use_heuristic": True, "person_id": able})
    assert logged_able.status_code == 200
    assert any(e["subtype"] == "vomiting" for e in logged_able.json()["events"])
    assert logged_able.json()["similar"]
    blocked = client.post("/log", json={"transcript": able_line, "use_heuristic": True}, headers={"X-Demo-Role": "clinician"})
    assert blocked.status_code == 403
print("closed loop OK (text path + Able + role guard)")
PY

echo "== live Ollama (optional) =="
python -m pytest tests/ -m live -q || echo "live tests skipped or failed (start ollama and pull llama3.2:3b)"

echo "All verification steps finished."
