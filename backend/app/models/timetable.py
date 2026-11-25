from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class AcademicCodeMapping(Base):
    __tablename__ = "academic_code_mappings"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. "SE", "TE", "BE", "ST", "TT", "BT"
    full_name = Column(String(150), nullable=False) # e.g. "Second Year B.Tech", "Third Year B.Tech"
    category = Column(String(50), default="Year", nullable=False) # Year, Programme, Shift
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TimetableUpload(Base):
    __tablename__ = "timetable_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    total_pages = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="Uploaded", nullable=False) # Uploaded, Processing, Reviewed, Confirmed, Failed
    records_count = Column(Integer, default=0, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processing_notes = Column(Text, nullable=True)

    records = relationship("TimetableRecord", back_populates="upload", cascade="all, delete-orphan")

class TimetableRecord(Base):
    __tablename__ = "timetable_records"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("timetable_uploads.id", ondelete="SET NULL"), nullable=True)
    
    # Examination metadata
    exam_name = Column(String(150), nullable=False) # e.g. "End Semester Examination Winter 2026"
    department_name = Column(String(100), nullable=False) # e.g. "AI&DS", "IT", "COMP"
    programme = Column(String(100), nullable=True) # e.g. "B.Tech Artificial Intelligence & Data Science"
    academic_year = Column(String(50), nullable=False) # e.g. "SE", "TE", "BE"
    semester = Column(String(50), nullable=False) # e.g. "Semester III"
    
    # Subject metadata
    subject_name = Column(String(150), nullable=False) # e.g. "Database Management Systems"
    subject_code = Column(String(50), nullable=False, index=True) # e.g. "AID301"
    
    # Schedule
    exam_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(20), nullable=False) # e.g. "10:30 AM"
    end_time = Column(String(20), nullable=False) # e.g. "01:30 PM"
    shift_name = Column(String(50), default="Morning Shift", nullable=True) # "Morning Shift" or "Evening Shift"
    duration = Column(String(50), nullable=True) # e.g. "2 Hours", "1.5 Hours", "3 Hours"
    
    # Extraction Confidence & Verification
    confidence_score = Column(Integer, default=95) # 0-100% OCR confidence
    is_confirmed = Column(Boolean, default=False, nullable=False)
    notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    upload = relationship("TimetableUpload", back_populates="records")
