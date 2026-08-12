from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PersonProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    conditions: str
    allergies: str = ""
    relationship: str = "father"


class MedicationSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    dose: str
    times_per_day: int = 1
    scheduled_times: str
    start_date: datetime
    last_changed_at: Optional[datetime] = None


class CareEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    logged_at: datetime
    event_time: datetime
    type: str
    subtype: str
    detail: str = ""
    raw_transcript: str = ""
    confidence: float = 1.0
    urgent: bool = False


class PatternFlag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime
    kind: str
    subtype: str = ""
    message: str
    related_date: Optional[datetime] = None


class Brief(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime
    kind: str = "gp"
    markdown: str
    pdf_path: str = ""
    period_start: datetime
    period_end: datetime
