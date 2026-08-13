from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    display_name: str
    role: str = "support_worker"


class PersonProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    conditions: str
    allergies: str = ""
    relationship: str = "father"


class MedicationSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    person_id: Optional[int] = Field(default=None, index=True)
    name: str
    dose: str
    times_per_day: int = 1
    scheduled_times: str
    start_date: datetime
    last_changed_at: Optional[datetime] = None


class Shift(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    started_at: datetime
    ended_at: Optional[datetime] = None


class CareEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    person_id: Optional[int] = Field(default=None, index=True)
    logger_id: Optional[int] = Field(default=None, index=True)
    shift_id: Optional[int] = Field(default=None, index=True)
    logged_at: datetime
    event_time: datetime = Field(index=True)
    type: str
    subtype: str
    detail: str = ""
    raw_transcript: str = ""
    confidence: float = 1.0
    urgent: bool = False


class PatternFlag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    person_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime
    kind: str
    subtype: str = ""
    message: str
    related_date: Optional[datetime] = None
    evidence_event_ids: str = ""


class Brief(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    person_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime
    kind: str = "gp"
    markdown: str
    pdf_path: str = ""
    period_start: datetime
    period_end: datetime
