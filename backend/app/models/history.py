from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class FacultyDutyHistory(Base):
    __tablename__ = "faculty_duty_history"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    exam_name = Column(String(150), nullable=False)
    academic_year = Column(String(50), nullable=True)
    semester = Column(String(50), nullable=True)
    exam_date = Column(Date, nullable=False, index=True)
    shift_name = Column(String(50), nullable=False)
    exam_timing = Column(String(100), nullable=True) # e.g. "10:30 AM - 01:30 PM"
    role_served = Column(String(50), nullable=False) # 'JS', 'Reliever', 'Standby', 'SS'
    block_or_room = Column(String(100), nullable=True)
    status = Column(String(30), default="Approved", nullable=False)
    is_manual_override = Column(Boolean, default=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    faculty = relationship("Faculty", back_populates="duty_histories")

class FacultyAvailability(Base):
    __tablename__ = "faculty_availability"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    # Available, On Leave, Unavailable, Official Duty, Exempted, Other
    status = Column(String(50), default="Available", nullable=False)
    reason = Column(String(255), nullable=True) # Medical leave, On duty external, Research leave, etc.
    recorded_by = Column(String(100), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    faculty = relationship("Faculty", back_populates="availabilities")
