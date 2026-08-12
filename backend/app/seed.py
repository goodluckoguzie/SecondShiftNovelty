from datetime import datetime

from sqlmodel import Session, select

from .models import CareEvent, MedicationSchedule, PersonProfile

DEMO_WEEK_END = datetime(2026, 8, 11, 23, 59)
DOSE_CHANGE = datetime(2026, 8, 7, 9, 0)


def seed_if_empty(session: Session) -> None:
    if session.exec(select(PersonProfile)).first():
        return

    session.add(
        PersonProfile(
            name="Dad",
            age=71,
            conditions="dementia",
            allergies="none known",
            relationship="father",
        )
    )
    session.add_all(
        [
            MedicationSchedule(
                name="Donepezil",
                dose="10mg",
                times_per_day=1,
                scheduled_times="20:00",
                start_date=datetime(2026, 7, 1),
                last_changed_at=DOSE_CHANGE,
            ),
            MedicationSchedule(
                name="Ramipril",
                dose="5mg",
                times_per_day=1,
                scheduled_times="08:00",
                start_date=datetime(2026, 6, 1),
            ),
            MedicationSchedule(
                name="Atorvastatin",
                dose="20mg",
                times_per_day=1,
                scheduled_times="20:00",
                start_date=datetime(2026, 6, 1),
            ),
        ]
    )

    events = [
        CareEvent(
            logged_at=datetime(2026, 8, 8, 19, 20),
            event_time=datetime(2026, 8, 8, 19, 10),
            type="meal",
            subtype="appetite_low",
            detail="barely touched dinner",
            raw_transcript="He barely touched dinner.",
            confidence=0.95,
        ),
        CareEvent(
            logged_at=datetime(2026, 8, 9, 21, 0),
            event_time=datetime(2026, 8, 9, 20, 50),
            type="symptom",
            subtype="confusion",
            detail="agitated after the new tablet",
            raw_transcript="Agitated after the new tablet.",
            confidence=0.9,
        ),
        CareEvent(
            logged_at=datetime(2026, 8, 9, 19, 15),
            event_time=datetime(2026, 8, 9, 19, 5),
            type="meal",
            subtype="appetite_low",
            detail="left most of his supper",
            raw_transcript="Left most of his supper.",
            confidence=0.92,
        ),
        CareEvent(
            logged_at=datetime(2026, 8, 10, 21, 10),
            event_time=datetime(2026, 8, 10, 21, 5),
            type="symptom",
            subtype="confusion",
            detail="did not recognise me for a few minutes",
            raw_transcript="Didn't recognise me for a few minutes.",
            confidence=0.93,
        ),
        CareEvent(
            logged_at=datetime(2026, 8, 10, 20, 55),
            event_time=datetime(2026, 8, 10, 20, 45),
            type="medication",
            subtype="dose_late",
            detail="evening medicines 45 minutes late",
            raw_transcript="Evening pills about 45 minutes late.",
            confidence=0.94,
        ),
        CareEvent(
            logged_at=datetime(2026, 8, 10, 19, 20),
            event_time=datetime(2026, 8, 10, 19, 10),
            type="meal",
            subtype="appetite_low",
            detail="picked at dinner",
            raw_transcript="He only picked at dinner.",
            confidence=0.9,
        ),
        CareEvent(
            logged_at=datetime(2026, 8, 11, 20, 55),
            event_time=datetime(2026, 8, 11, 20, 40),
            type="medication",
            subtype="dose_late",
            detail="evening medicines 40 minutes late",
            raw_transcript="Gave dad his 8pm meds, 40 minutes late.",
            confidence=0.95,
        ),
        CareEvent(
            logged_at=datetime(2026, 8, 11, 19, 15),
            event_time=datetime(2026, 8, 11, 19, 5),
            type="meal",
            subtype="appetite_low",
            detail="barely touched dinner",
            raw_transcript="Barely touched dinner again.",
            confidence=0.91,
        ),
    ]
    session.add_all(events)
    session.commit()
