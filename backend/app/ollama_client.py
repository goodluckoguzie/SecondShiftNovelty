from __future__ import annotations

import json
from typing import Any

import httpx

from .config import OLLAMA_HOST, OLLAMA_MODEL

EXTRACT_SYSTEM = """You are a care-log extraction engine for whoever is recording (family or support worker) for a person with dementia in the UK.
Extract care events from the carer's message. Output strict JSON only.
Never give medical advice, diagnosis, triage, or treatment suggestions.
If a medication time is ambiguous, set confidence below 0.7.

JSON shape:
{"events":[{"type":"medication|symptom|meal|sleep|mood|incident|note","subtype":"dose_late|dose_missed|confusion|agitation|appetite_low|vomiting|eaten|mood_low|note","event_time":"ISO-8601 if known else null","detail":"short","confidence":0.0}],"clarifying_question":null,"confirmation":"short UK English confirmation"}
"""

QUESTIONS_SYSTEM = """You draft 3 to 5 short questions a family carer can ask a GP or memory clinic.
Use only the structured evidence provided. Do not diagnose. Output JSON: {"questions":["..."]}
"""


def chat_json(prompt: str, system: str, model: str | None = None, timeout: float = 120.0) -> dict[str, Any]:
    payload = {
        "model": model or OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        response.raise_for_status()
        content = response.json()["message"]["content"]
    return json.loads(content)


def ollama_available() -> bool:
    try:
        with httpx.Client(timeout=2.0) as client:
            return client.get(f"{OLLAMA_HOST}/api/tags").status_code == 200
    except Exception:
        return False
