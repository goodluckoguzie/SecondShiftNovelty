from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app
from app.seed import seed_if_empty
from app.patterns import recompute_flags


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)

    def override_session():
        with Session(test_engine) as session:
            yield session

    from app.main import get_session

    app.router.on_startup.clear()
    app.dependency_overrides[get_session] = override_session
    with Session(test_engine) as session:
        seed_if_empty(session)
        recompute_flags(session)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
