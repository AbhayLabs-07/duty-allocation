from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class UploadedDutyChart(Base):
    __tablename__ = "uploaded_duty_charts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) # excel, docx, pdf, image
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), default="Pending Verification", nullable=False) # Pending Verification, Verified, Processed, Rejected
    total_records_extracted = Column(Integer, default=0, nullable=False)
    detected_exam_name = Column(String(150), nullable=True)
    detected_exam_year = Column(String(50), nullable=True)
    detected_semester = Column(String(50), nullable=True)
    detected_exam_date = Column(Date, nullable=True)
    detected_shift = Column(String(50), nullable=True)
    detected_block_count = Column(Integer, nullable=True)
    detected_rooms = Column(String(500), nullable=True)
    raw_metadata_json = Column(Text, nullable=True)

    extracted_records = relationship("ExtractedDutyRecord", back_populates="upload", cascade="all, delete-orphan")

class ExtractedDutyRecord(Base):
    __tablename__ = "extracted_duty_records"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploaded_duty_charts.id", ondelete="CASCADE"), nullable=False)
    
    # Raw values extracted from doc/OCR
    raw_faculty_name = Column(String(150), nullable=False)
    raw_department = Column(String(100), nullable=True)
    raw_date = Column(String(50), nullable=True)
    raw_shift = Column(String(50), nullable=True)
    raw_duty_role = Column(String(50), nullable=True) # JS, Reliever, Standby, SS
    raw_total_duty = Column(Integer, nullable=True)
    
    # Verified / Mapped values
    matched_faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    matched_faculty_name = Column(String(150), nullable=True)
    matched_department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    verified_duty_role = Column(String(50), nullable=True)
    confidence_score = Column(Integer, default=100) # 0-100% OCR / match confidence
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_notes = Column(String(255), nullable=True)

    upload = relationship("UploadedDutyChart", back_populates="extracted_records")
    faculty = relationship("Faculty")
    department = relationship("Department")
