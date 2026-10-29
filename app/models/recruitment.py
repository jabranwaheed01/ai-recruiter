
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    job_title = Column(String(150), nullable=True)

    # Date of birth in YYYY-MM-DD format
    dob = Column(String(10), nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    calls = relationship("Call", back_populates="candidate")


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)

    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=False,
    )

    vapi_call_id = Column(String(100), nullable=True, unique=True)
    assistant_id = Column(String(100), nullable=True)
    status = Column(String(30), default="Pending", nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    transcript = Column(Text, nullable=True)
    recording_url = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    candidate = relationship("Candidate", back_populates="calls")

    result = relationship(
        "CallResult",
        back_populates="call",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CallResult(Base):
    __tablename__ = "call_results"

    id = Column(Integer, primary_key=True, index=True)

    call_id = Column(
        Integer,
        ForeignKey("calls.id"),
        nullable=False,
        unique=True,
    )

    outcome = Column(String(30), default="Pending", nullable=False)
    dob_verified = Column(String(10), nullable=True)
    eligible = Column(String(10), nullable=True)
    notes = Column(Text, nullable=True)
    interview_datetime = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    call = relationship("Call", back_populates="result")
