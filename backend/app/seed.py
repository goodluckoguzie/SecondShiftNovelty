from datetime import datetime

from sqlmodel import Session, select

from .models import CareEvent, MedicationSchedule, PersonProfile, User

DOSE_CHANGE = datetime(2026, 8, 7, 9, 0)

WORKERS = ("Goodluck", "Abene", "Pelumi", "Okunola", "Kemi")

PATIENTS = (
    ("Dad", 71, "father"),
    ("Able", 78, "resident"),
    ("Margaret", 84, "resident"),
    ("Harold", 80, "resident"),
    ("Joyce", 76, "resident"),
    ("Ibrahim", 73, "resident"),
    ("Evelyn", 88, "resident"),
    ("Frank", 82, "resident"),
    ("Aisha", 75, "resident"),
    ("George", 79, "resident"),
)


def seed_if_empty(session: Session) -> None:
    workers = _ensure_users(session)
    people = _ensure_people(session)
    _retire_old_demo_workers(session, workers)
    workers = {u.display_name: u for u in session.exec(select(User)).all()}
    _backfill_person_ids(session, people["Dad"])
    _seed_dad_if_needed(session, people["Dad"], workers["Goodluck"])
    _seed_able_if_needed(session, people["Able"], workers["Pelumi"])
    _seed_other_patients(session, people, workers)


def _ensure_users(session: Session) -> dict[str, User]:
    found = {u.display_name: u for u in session.exec(select(User)).all()}
    created = False
    for name in WORKERS:
        if name not in found:
            row = User(display_name=name, role="support_worker")
            session.add(row)
            created = True
    if "Dr Chen" not in found:
        session.add(User(display_name="Dr Chen", role="clinician"))
        created = True
    if created:
        session.commit()
    return {u.display_name: u for u in session.exec(select(User)).all()}


def _ensure_people(session: Session) -> dict[str, PersonProfile]:
    found = {p.name: p for p in session.exec(select(PersonProfile)).all()}
    created = False
    for name, age, relationship in PATIENTS:
        if name not in found:
            session.add(
                PersonProfile(
                    name=name,
                    age=age,
                    conditions="dementia",
                    allergies="none known",
                    relationship=relationship,
                )
            )
            created = True
    if created:
        session.commit()
    return {p.name: p for p in session.exec(select(PersonProfile)).all()}


def _retire_old_demo_workers(session: Session, workers: dict[str, User]) -> None:
    keep = set(WORKERS) | {"Dr Chen"}
    fallback = workers.get("Goodluck")
    if not fallback:
        return
    leftover = [u for u in session.exec(select(User)).all() if u.display_name not in keep]
    if not leftover:
        return
    leftover_ids = {u.id for u in leftover}
    for event in session.exec(select(CareEvent)).all():
        if event.logger_id in leftover_ids:
            event.logger_id = fallback.id
            session.add(event)
    for row in leftover:
        session.delete(row)
    session.commit()


def _has_events(session: Session, person_id: int) -> bool:
    return session.exec(select(CareEvent).where(CareEvent.person_id == person_id)).first() is not None


def _seed_dad_if_needed(session: Session, dad: PersonProfile, logger: User) -> None:
    meds = session.exec(select(MedicationSchedule).where(MedicationSchedule.person_id == dad.id)).all()
    if not meds:
        session.add_all(
            [
                MedicationSchedule(
                    person_id=dad.id,
                    name="Donepezil",
                    dose="10mg",
                    times_per_day=1,
                    scheduled_times="20:00",
                    start_date=datetime(2026, 7, 1),
                    last_changed_at=DOSE_CHANGE,
                ),
                MedicationSchedule(
                    person_id=dad.id,
                    name="Ramipril",
                    dose="5mg",
                    times_per_day=1,
                    scheduled_times="08:00",
                    start_date=datetime(2026, 6, 1),
                ),
                MedicationSchedule(
                    person_id=dad.id,
                    name="Atorvastatin",
                    dose="20mg",
                    times_per_day=1,
                    scheduled_times="20:00",
                    start_date=datetime(2026, 6, 1),
                ),
            ]
        )
        session.commit()
    if _has_events(session, dad.id):
        return
    session.add_all(
        [
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 8, 19, 20),
                event_time=datetime(2026, 8, 8, 19, 10),
                type="meal",
                subtype="appetite_low",
                detail="barely touched dinner",
                raw_transcript="He barely touched dinner.",
                confidence=0.95,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 9, 21, 0),
                event_time=datetime(2026, 8, 9, 20, 50),
                type="symptom",
                subtype="confusion",
                detail="agitated after the new tablet",
                raw_transcript="Agitated after the new tablet.",
                confidence=0.9,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 9, 19, 15),
                event_time=datetime(2026, 8, 9, 19, 5),
                type="meal",
                subtype="appetite_low",
                detail="left most of his supper",
                raw_transcript="Left most of his supper.",
                confidence=0.92,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 10, 21, 10),
                event_time=datetime(2026, 8, 10, 21, 5),
                type="symptom",
                subtype="confusion",
                detail="did not recognise me for a few minutes",
                raw_transcript="Didn't recognise me for a few minutes.",
                confidence=0.93,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 10, 20, 55),
                event_time=datetime(2026, 8, 10, 20, 45),
                type="medication",
                subtype="dose_late",
                detail="evening medicines 45 minutes late",
                raw_transcript="Evening pills about 45 minutes late.",
                confidence=0.94,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 10, 19, 20),
                event_time=datetime(2026, 8, 10, 19, 10),
                type="meal",
                subtype="appetite_low",
                detail="picked at dinner",
                raw_transcript="He only picked at dinner.",
                confidence=0.9,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 11, 20, 55),
                event_time=datetime(2026, 8, 11, 20, 40),
                type="medication",
                subtype="dose_late",
                detail="evening medicines 40 minutes late",
                raw_transcript="Gave dad his 8pm meds, 40 minutes late.",
                confidence=0.95,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 11, 19, 15),
                event_time=datetime(2026, 8, 11, 19, 5),
                type="meal",
                subtype="appetite_low",
                detail="barely touched dinner",
                raw_transcript="Barely touched dinner again.",
                confidence=0.91,
            ),
        ]
    )
    session.commit()


def _seed_able_if_needed(session: Session, able: PersonProfile, logger: User) -> None:
    if _has_events(session, able.id):
        return
    session.add_all(
        [
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 7, 20, 10),
                event_time=datetime(2026, 8, 7, 19, 40),
                type="meal",
                subtype="eaten",
                detail="ate supper",
                raw_transcript="Able has eaten his supper.",
                confidence=0.9,
            ),
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 7, 20, 20),
                event_time=datetime(2026, 8, 7, 20, 5),
                type="symptom",
                subtype="vomiting",
                detail="vomited after supper",
                raw_transcript="After eating he was vomiting.",
                confidence=0.92,
            ),
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 8, 9, 10),
                event_time=datetime(2026, 8, 8, 8, 40),
                type="meal",
                subtype="eaten",
                detail="ate breakfast",
                raw_transcript="Able ate breakfast.",
                confidence=0.88,
            ),
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 8, 9, 20),
                event_time=datetime(2026, 8, 8, 9, 0),
                type="symptom",
                subtype="vomiting",
                detail="vomited after breakfast",
                raw_transcript="He was sick again after food this morning.",
                confidence=0.91,
            ),
        ]
    )
    session.commit()


def _seed_other_patients(session: Session, people: dict[str, PersonProfile], workers: dict[str, User]) -> None:
    extras = [
        (
            "Margaret",
            workers["Abene"],
            [
                (datetime(2026, 8, 10, 8, 15), "meal", "eaten", "ate porridge", "Margaret ate her porridge."),
                (datetime(2026, 8, 11, 21, 0), "mood", "mood_low", "quiet and withdrawn", "Margaret was very quiet this evening."),
            ],
        ),
        (
            "Harold",
            workers["Okunola"],
            [
                (datetime(2026, 8, 9, 20, 20), "medication", "dose_late", "evening medicines 20 minutes late", "Harold's 8pm meds were 20 minutes late."),
                (datetime(2026, 8, 11, 7, 40), "symptom", "agitation", "restless at breakfast", "Harold was restless at breakfast."),
            ],
        ),
        (
            "Joyce",
            workers["Kemi"],
            [
                (datetime(2026, 8, 8, 19, 0), "meal", "appetite_low", "left most of supper", "Joyce left most of her supper."),
                (datetime(2026, 8, 10, 19, 10), "meal", "appetite_low", "picked at dinner", "Joyce only picked at dinner."),
            ],
        ),
        (
            "Ibrahim",
            workers["Goodluck"],
            [
                (datetime(2026, 8, 10, 14, 0), "symptom", "confusion", "did not know where he was", "Ibrahim did not know where he was after lunch."),
                (datetime(2026, 8, 11, 14, 20), "note", "note", "slept after lunch", "Ibrahim slept after lunch."),
            ],
        ),
        (
            "Evelyn",
            workers["Pelumi"],
            [
                (datetime(2026, 8, 9, 22, 0), "sleep", "note", "settled late", "Evelyn settled late, about 10pm."),
                (datetime(2026, 8, 11, 8, 10), "meal", "eaten", "ate breakfast", "Evelyn ate breakfast."),
            ],
        ),
        (
            "Frank",
            workers["Abene"],
            [
                (datetime(2026, 8, 8, 11, 0), "incident", "note", "needed two staff to stand", "Frank needed two of us to stand from the chair."),
                (datetime(2026, 8, 11, 16, 30), "mood", "mood_low", "tearful in the lounge", "Frank was tearful in the lounge."),
            ],
        ),
        (
            "Aisha",
            workers["Kemi"],
            [
                (datetime(2026, 8, 10, 9, 0), "meal", "eaten", "ate breakfast", "Aisha ate breakfast well."),
                (datetime(2026, 8, 11, 20, 10), "medication", "note", "evening medicines given on time", "Aisha took her 8pm meds on time."),
            ],
        ),
        (
            "George",
            workers["Okunola"],
            [
                (datetime(2026, 8, 9, 19, 30), "symptom", "confusion", "asked for his wife", "George asked for his wife several times."),
                (datetime(2026, 8, 11, 19, 40), "symptom", "confusion", "asked for his wife again", "George asked for his wife again this evening."),
            ],
        ),
    ]
    added = []
    for name, logger, rows in extras:
        person = people[name]
        if _has_events(session, person.id):
            continue
        for when, typ, subtype, detail, quote in rows:
            added.append(
                CareEvent(
                    person_id=person.id,
                    logger_id=logger.id,
                    logged_at=when,
                    event_time=when,
                    type=typ,
                    subtype=subtype,
                    detail=detail,
                    raw_transcript=quote,
                    confidence=0.9,
                )
            )
    if added:
        session.add_all(added)
        session.commit()


def _backfill_person_ids(session: Session, dad: PersonProfile) -> None:
    changed = False
    for event in session.exec(select(CareEvent)).all():
        if event.person_id is None:
            event.person_id = dad.id
            session.add(event)
            changed = True
    for med in session.exec(select(MedicationSchedule)).all():
        if med.person_id is None:
            med.person_id = dad.id
            session.add(med)
            changed = True
    if changed:
        session.commit()
