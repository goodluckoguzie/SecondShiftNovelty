#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

WEB_URL="${WEB_URL:-http://127.0.0.1:8080}"
API_URL="${API_URL:-http://127.0.0.1:8080/api}"

COMPOSE="docker-compose"
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
fi

echo "== Second Shift Docker =="
echo "Building and starting api + web + ollama..."
$COMPOSE up --build -d

echo "Waiting for API health..."
ok=0
for i in $(seq 1 90); do
  if curl -fsS "$API_URL/health" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 2
done
if [ "$ok" != "1" ]; then
  echo "API did not become healthy. Logs:"
  $COMPOSE logs --tail=80 api
  exit 1
fi

echo "Verifying closed loop via API..."
python3 - <<PY
import json, urllib.request

api = "${API_URL}"

def req(method, path, data=None):
    body = None if data is None else json.dumps(data).encode()
    r = urllib.request.Request(api + path, data=body, method=method)
    if data is not None:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=60) as resp:
        raw = resp.read()
        if resp.headers.get_content_type() == "application/json":
            return json.loads(raw)
        return raw

health = req("GET", "/health")
assert health.get("ok") is True, health
print("health OK", health)

ravi = "Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week."
logged = req("POST", "/log", {"transcript": ravi, "use_heuristic": True})
assert logged.get("emergency") is False, logged
assert any(f.get("kind") == "symptom_recurrence" for f in logged.get("flags", [])), logged.get("flags")
print("log + pattern flag OK")

brief = req("POST", "/briefs")
assert "[log " in brief.get("markdown", ""), brief
pdf = req("GET", "/briefs/latest.pdf")
assert pdf[:4] == b"%PDF", pdf[:20]
print("GP brief PDF OK")

handover = req("POST", "/handover", {"name": "your sister"})
assert "72" in handover.get("markdown", "")
hpdf = req("GET", "/handover/latest.pdf")
assert hpdf[:4] == b"%PDF"
print("handover PDF OK")

board = req("GET", "/board")
assert len(board.get("people") or []) >= 10, board
print("wing board OK")

people = req("GET", "/people")
frank = next(p for p in people if p["name"] == "Frank")
tearful = req("POST", "/log", {"transcript": "He was tearful in the lounge.", "use_heuristic": True, "person_id": frank["id"]})
assert any(e.get("type") == "mood" for e in tearful.get("events") or []), tearful
print("tearful mood OK")

corridor = req("POST", "/log/corridor", {"transcript": "Able up at two. Frank was tearful.", "use_heuristic": True})
assert {s.get("person_name") for s in corridor.get("slices") or []} == {"Able", "Frank"}
print("corridor dump OK")

users = req("GET", "/users")
ravi = next(u for u in users if u.get("role") == "family")
dad = next(p for p in people if p["name"] == "Dad")
home = urllib.request.Request(
    api + "/log",
    data=json.dumps({
        "transcript": "Barely touched his tea.",
        "use_heuristic": True,
        "person_id": dad["id"],
        "logger_id": ravi["id"],
    }).encode(),
    method="POST",
    headers={"Content-Type": "application/json", "X-Demo-Role": "family"},
)
with urllib.request.urlopen(home, timeout=60) as resp:
    family_log = json.loads(resp.read())
assert family_log["events"][0]["source"] == "from_home"
print("family from_home OK")

brief2 = req("POST", "/briefs", {"person_id": dad["id"]})
assert "## From the shift" in brief2.get("markdown", "")
assert "## From home" in brief2.get("markdown", "")
print("two-column GP brief OK")
PY

echo "Verifying web UI..."
curl -fsS "$WEB_URL/" | grep -q "Second Shift"
curl -fsS "$WEB_URL/api/health" | grep -q '"ok"'
echo "web + /api proxy OK"

echo "Pulling Ollama model llama3.2:3b (first time can take a few minutes)..."
$COMPOSE exec -T ollama ollama pull llama3.2:3b || echo "Ollama pull skipped or still starting; typed logging still works."

echo
echo "Ready."
echo "  App:  $WEB_URL"
echo "  API:  $API_URL/health"
echo "  Stop: $COMPOSE down"
echo
echo "Demo: open the app, type the Ravi sentence, click Log text."
