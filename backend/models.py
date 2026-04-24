# backend/models.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(150), nullable=False)
    email        = Column(String(200), unique=True, nullable=False, index=True)
    password_hash= Column(String(255), nullable=False)
    created_at   = Column(DateTime, server_default=func.now())
    registrations = relationship("Registration", back_populates="user")

class Event(Base):
    __tablename__ = "events"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text)
    event_date  = Column(Date, nullable=False)
    image_url   = Column(Text)
    capacity    = Column(Integer, default=100)
    deadline    = Column(Date)
    created_at  = Column(DateTime, server_default=func.now())
    event_fields        = relationship("EventField",        back_populates="event", cascade="all, delete-orphan")
    registration_fields = relationship("RegistrationField", back_populates="event", cascade="all, delete-orphan")
    registrations       = relationship("Registration",      back_populates="event", cascade="all, delete-orphan")

class EventField(Base):
    __tablename__ = "event_fields"
    id          = Column(Integer, primary_key=True, index=True)
    event_id    = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    field_name  = Column(String(100), nullable=False)
    field_type  = Column(String(20),  default="text")
    field_value = Column(Text)
    event       = relationship("Event", back_populates="event_fields")

class RegistrationField(Base):
    __tablename__ = "registration_fields"
    id          = Column(Integer, primary_key=True, index=True)
    event_id    = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    field_name  = Column(String(100), nullable=False)
    field_type  = Column(String(20),  default="text")
    is_required = Column(Integer, default=1)
    options     = Column(Text)
    event       = relationship("Event", back_populates="registration_fields")
    answers     = relationship("RegistrationAnswer", back_populates="field", cascade="all, delete-orphan")

class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("prn", "event_id", name="uq_prn_event"),)

    id         = Column(Integer, primary_key=True, index=True)
    event_id   = Column(Integer, ForeignKey("events.id",  ondelete="CASCADE"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id",   ondelete="SET NULL"), nullable=True)
    name       = Column(String(150), nullable=False)
    prn        = Column(String(50),  nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    event   = relationship("Event", back_populates="registrations")
    user    = relationship("User",  back_populates="registrations")
    answers = relationship(
        "RegistrationAnswer",
        back_populates="registration",
        cascade="all, delete-orphan"
    )

class RegistrationAnswer(Base):
    __tablename__ = "registration_answers"
    id              = Column(Integer, primary_key=True, index=True)
    registration_id = Column(Integer, ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    field_id        = Column(Integer, ForeignKey("registration_fields.id", ondelete="CASCADE"), nullable=False)
    value           = Column(Text)
    registration = relationship("Registration", back_populates="answers")
    field        = relationship("RegistrationField", back_populates="answers")