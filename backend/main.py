# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date as Date
from backend import models, auth
from backend.database import engine, get_db, Base


try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print("DB INIT ERROR:", e)

app = FastAPI(title="CampusEvents API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten to your Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── SCHEMAS ──────────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    name:     str
    email:    EmailStr
    password: str

class LoginIn(BaseModel):
    email:    EmailStr
    password: str

class EventRegisterIn(BaseModel):
    name:    str
    prn:     str
    answers: dict[int, str] = {}  # {field_id: value}

# ── HEALTH ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/api/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(400, "Email already registered")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    user = models.User(
        name=body.name.strip(),
        email=body.email.lower().strip(),
        password_hash=auth.hash_password(body.password),
    )
    db.add(user); db.commit(); db.refresh(user)
    token = auth.create_token(user.id, user.email)
    return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email.lower()).first()
    if not user or not auth.verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    token = auth.create_token(user.id, user.email)
    return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.get("/api/auth/me")
def me(current_user: models.User = Depends(auth.get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email,
            "created_at": str(current_user.created_at)}

# ══════════════════════════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/events")
def list_events(
    search: str = Query("", alias="q"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_optional_user),
):
    query = db.query(models.Event)
    if search.strip():
        like = f"%{search.strip()}%"
        query = query.filter(
            models.Event.title.ilike(like) | models.Event.description.ilike(like)
        )
    events = query.order_by(models.Event.event_date.asc()).all()

    # Registered event ids for current user
    registered_ids = set()
    if current_user:
        user_regs = db.query(models.Registration.event_id).filter(
            models.Registration.user_id == current_user.id
        ).all()
        registered_ids = {r.event_id for r in user_regs}

    result = []
    for e in events:
        reg_count = db.query(models.Registration).filter(models.Registration.event_id == e.id).count()
        result.append({
            "id":           e.id,
            "title":        e.title,
            "description":  e.description,
            "event_date":   str(e.event_date),
            "image_url":    e.image_url,
            "capacity":     e.capacity,
            "deadline":     str(e.deadline) if e.deadline else None,
            "created_at":   str(e.created_at),
            "reg_count":    reg_count,
            "spots_left":   max(0, e.capacity - reg_count),
            "is_full":      reg_count >= e.capacity,
            "is_registered": e.id in registered_ids,
            "is_past":      e.event_date < date_today(),
            "deadline_passed": bool(e.deadline and e.deadline < date_today()),
            "event_fields": [
                {"field_name": f.field_name, "field_type": f.field_type, "field_value": f.field_value}
                for f in e.event_fields
            ],
        })
    return result

@app.get("/api/events/{event_id}")
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_optional_user),
):
    e = db.query(models.Event).options(
        joinedload(models.Event.event_fields),
        joinedload(models.Event.registration_fields),
    ).filter(models.Event.id == event_id).first()

    if not e:
        raise HTTPException(404, "Event not found")

    reg_count = db.query(models.Registration).filter(models.Registration.event_id == e.id).count()
    is_registered = False
    if current_user:
        is_registered = db.query(models.Registration).filter(
            models.Registration.event_id == event_id,
            models.Registration.user_id  == current_user.id,
        ).first() is not None

    return {
        "id":           e.id,
        "title":        e.title,
        "description":  e.description,
        "event_date":   str(e.event_date),
        "image_url":    e.image_url,
        "capacity":     e.capacity,
        "deadline":     str(e.deadline) if e.deadline else None,
        "created_at":   str(e.created_at),
        "reg_count":    reg_count,
        "spots_left":   max(0, e.capacity - reg_count),
        "is_full":      reg_count >= e.capacity,
        "is_registered": is_registered,
        "is_past":      e.event_date < date_today(),
        "deadline_passed": bool(e.deadline and e.deadline < date_today()),
        "event_fields": [
            {"id": f.id, "field_name": f.field_name, "field_type": f.field_type, "field_value": f.field_value}
            for f in e.event_fields
        ],
        "registration_fields": [
            {
                "id":          f.id,
                "field_name":  f.field_name,
                "field_type":  f.field_type,
                "is_required": bool(f.is_required),
                "options":     [o.strip() for o in f.options.split(",")] if f.options else [],
            }
            for f in e.registration_fields
        ],
    }

# ══════════════════════════════════════════════════════════════════════════════
#  REGISTRATIONS
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/api/events/{event_id}/register")
def register_for_event(
    event_id: int,
    body: EventRegisterIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    # Deadline check
    if event.deadline and event.deadline < date_today():
        raise HTTPException(400, "Registration deadline has passed")

    # Already registered? — check by user_id (reliable) then fall back to PRN
    existing = db.query(models.Registration).filter(
        models.Registration.event_id == event_id,
        models.Registration.user_id  == current_user.id,
    ).first()
    if existing:
        raise HTTPException(409, "You are already registered for this event")

    # Atomic capacity check
    result = db.execute(text("""
        UPDATE events
        SET capacity = capacity
        WHERE id = :eid
        AND (SELECT COUNT(*) FROM registrations WHERE event_id = :eid) < capacity
    """), {"eid": event_id})

    reg_count = db.query(models.Registration).filter(models.Registration.event_id == event_id).count()
    if reg_count >= event.capacity:
        raise HTTPException(400, "Event is full")

    # Validate required fields
    reg_fields = db.query(models.RegistrationField).filter(
        models.RegistrationField.event_id == event_id
    ).all()
    for f in reg_fields:
        if f.is_required and not body.answers.get(f.id, "").strip():
            raise HTTPException(400, f"Field '{f.field_name}' is required")

    # Insert registration — save user_id so profile page can fetch it
    reg = models.Registration(
        event_id=event_id,
        user_id=current_user.id,
        name=body.name.strip(),
        prn=body.prn.strip().upper(),
    )
    db.add(reg)
    db.flush()

    # Insert answers
    for field_id, value in body.answers.items():
        if value and value.strip():
            db.add(models.RegistrationAnswer(
                registration_id=reg.id,
                field_id=int(field_id),
                value=value.strip(),
            ))
    db.commit()
    return {"message": "Registered successfully", "registration_id": reg.id}

@app.get("/api/my-registrations")
def my_registrations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    regs = db.query(models.Registration).options(
        joinedload(models.Registration.event),
        joinedload(models.Registration.answers).joinedload(models.RegistrationAnswer.field),
    ).filter(models.Registration.user_id == current_user.id).order_by(
        models.Registration.created_at.desc()
    ).all()

    result = []
    for r in regs:
        result.append({
            "id":           r.id,
            "name":         r.name,
            "prn":          r.prn,
            "created_at":   str(r.created_at),
            "event": {
                "id":         r.event.id,
                "title":      r.event.title,
                "event_date": str(r.event.event_date),
                "image_url":  r.event.image_url,
                "is_past":    r.event.event_date < date_today(),
            },
            "answers": [
                {"field_name": a.field.field_name, "value": a.value}
                for a in r.answers if a.field
            ],
        })
    return result

@app.delete("/api/my-registrations/{reg_id}")
def cancel_registration(
    reg_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    reg = db.query(models.Registration).filter(
        models.Registration.id      == reg_id,
        models.Registration.user_id == current_user.id,   # ownership check
    ).first()
    if not reg:
        raise HTTPException(404, "Registration not found")
    event = db.query(models.Event).filter(models.Event.id == reg.event_id).first()
    if event and event.event_date <= date_today():
        raise HTTPException(400, "Cannot cancel registration for a past or ongoing event")
    db.delete(reg); db.commit()
    return {"message": "Registration cancelled"}

# ── HELPERS ──────────────────────────────────────────────────────────────────
from datetime import date as dt_date
def date_today() -> dt_date:
    return dt_date.today()