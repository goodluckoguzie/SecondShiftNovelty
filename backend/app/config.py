import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "secondshift.db"
CACHED_BRIEF_PDF = DATA_DIR / "cached_brief.pdf"
CACHED_HANDOVER_PDF = DATA_DIR / "cached_handover.pdf"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")

DISCLAIMER = (
    "Second Shift organises your notes. It is not a medical device "
    "and does not give medical advice."
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
FAMILY_PASSWORD = os.getenv("FAMILY_PASSWORD", ADMIN_PASSWORD)
STAFF_PASSWORD = os.getenv("STAFF_PASSWORD", ADMIN_PASSWORD)

EMERGENCY_PHRASES = (
    "unconscious",
    "not breathing",
    "severe chest pain",
)
