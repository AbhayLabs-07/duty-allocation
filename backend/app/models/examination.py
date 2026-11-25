from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False) # e.g. "End Semester Examination Winter 2026"
    academic_year = Column(String(20), nullable=False) # e.g. "2025-2026"
    semester = Column(String(20), nullable=False) # e.g. "Semester IV"
    exam_level = Column(String(50), nullable=False, default="Second Year") # First Year, Second Year, Third Year, Final Year
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dates = relationship("ExaminationDate", back_populates="examination", cascade="all, delete-orphan")

class ExaminationDate(Base):
    __tablename__ = "examination_dates"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    exam_date = Column(Date, nullable=False, index=True)
    day_name = Column(String(20), nullable=True) # Monday, Tuesday, etc.

    examination = relationship("Examination", back_populates="dates")
    shifts = relationship("ExaminationShift", back_populates="exam_date_rel", cascade="all, delete-orphan")

class ExaminationShift(Base):
    __tablename__ = "examination_shifts"

    id = Column(Integer, primary_key=True, index=True)
    exam_date_id = Column(Integer, ForeignKey("examination_dates.id", ondelete="CASCADE"), nullable=False)
    shift_name = Column(String(50), nullable=False) # Morning, Afternoon, Evening
    start_time = Column(String(10), nullable=True) # e.g. "10:00 AM"
    end_time = Column(String(10), nullable=True) # e.g. "01:00 PM"
    block_count = Column(Integer, default=0, nullable=False) # Number of classroom blocks
    room_list_str = Column(String(500), nullable=True) # Comma-separated list of room numbers
    status = Column(String(30), default="Scheduled", nullable=False) # Scheduled, Allocated, Approved, Published

    exam_date_rel = relationship("ExaminationDate", back_populates="shifts")
    rooms = relationship("ExaminationRoom", back_populates="shift", cascade="all, delete-orphan")
    allocations = relationship("DutyAllocation", back_populates="shift", cascade="all, delete-orphan")

class ExaminationRoom(Base):
    __tablename__ = "examination_rooms"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("examination_shifts.id", ondelete="CASCADE"), nullable=False)
    block_number = Column(Integer, nullable=False)
    room_number = Column(String(50), nullable=False)
    block_label = Column(String(100), nullable=True) # e.g. "Block 1 (Room 101)"
    capacity = Column(Integer, default=30, nullable=False)
    floor = Column(String(20), nullable=True)
    building = Column(String(50), nullable=True)

    shift = relationship("ExaminationShift", back_populates="rooms")
