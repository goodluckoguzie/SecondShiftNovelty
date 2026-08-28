from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

from .config import DATA_DIR, DB_PATH
from .models import PersonProfile

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

_ALTERS = (
    ("personprofile", "id INTEGER"),
    ("personprofile", "usual VARCHAR"),
    ("personprofile", "risks VARCHAR"),
    ("personprofile", "mobility VARCHAR"),
    ("personprofile", "hospital_return_at DATETIME"),
    ("medicationschedule", "person_id INTEGER"),
    ("careevent", "person_id INTEGER"),
    ("careevent", "logger_id INTEGER"),
    ("careevent", "shift_id INTEGER"),
    ("careevent", "source VARCHAR"),
    ("careevent", "slots VARCHAR"),
    ("patternflag", "person_id INTEGER"),
    ("patternflag", "evidence_event_ids VARCHAR"),
    ("brief", "person_id INTEGER"),
    ("user", "family_person_id INTEGER"),
    ("user", "assigned_person_id INTEGER"),
)


def _migrate() -> None:
    with engine.begin() as conn:
        tables = {row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
        for table, decl in _ALTERS:
            if table not in tables:
                continue
            col = decl.split()[0]
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if col in existing:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {decl}"))


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    try:
        _migrate()
    except Exception:
        pass


def get_session():
    with Session(engine) as session:
        yield session


def resolve_person(session: Session, person_id: Optional[int] = None) -> PersonProfile:
    if person_id:
        person = session.get(PersonProfile, person_id)
        if not person:
            raise HTTPException(404, "No person")
        return person
    person = session.exec(select(PersonProfile).where(PersonProfile.name == "Dou")).first()
    if not person:
        person = session.exec(select(PersonProfile).where(PersonProfile.name == "Dad")).first()
    if not person:
        person = session.exec(select(PersonProfile)).first()
    if not person:
        raise HTTPException(404, "No profile")
    return person
