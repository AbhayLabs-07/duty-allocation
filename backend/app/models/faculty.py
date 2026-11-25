from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(String(50), unique=True, index=True, nullable=False) # e.g. FAC-CSE-001
    name = Column(String(150), index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    designation = Column(String(100), nullable=False) # Professor, Associate Professor, Assistant Professor
    role_category = Column(String(50), default="Faculty", nullable=False) # HOD, Dy. HOD, Faculty
    employment_status = Column(String(50), default="Regular", nullable=False) # Regular, Contract, Adjunct
    eligibility = Column(Boolean, default=True, nullable=False)
    joining_date = Column(Date, nullable=True)
    email = Column(String(150), nullable=True)
    phone = Column(String(30), nullable=True)
    
    # Historical duty counters (cached for fast fairness calculations, backed by FacultyDutyHistory)
    total_previous_duties = Column(Integer, default=0, nullable=False)
    previous_js_count = Column(Integer, default=0, nullable=False)
    previous_reliever_count = Column(Integer, default=0, nullable=False)
    previous_standby_count = Column(Integer, default=0, nullable=False)
    previous_ss_count = Column(Integer, default=0, nullable=False)

    # Adaptive fairness tracking
    last_assigned_role = Column(String(50), nullable=True) # Last assigned role: 'JS', 'Reliever', 'Standby', 'SS'
    last_assigned_date = Column(Date, nullable=True)
    current_cycle_duties = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    department = relationship("Department", back_populates="faculty_members")
    allocations = relationship("DutyAllocation", back_populates="faculty", cascade="all, delete-orphan")
    duty_histories = relationship("FacultyDutyHistory", back_populates="faculty", cascade="all, delete-orphan")
    availabilities = relationship("FacultyAvailability", back_populates="faculty", cascade="all, delete-orphan")
    batch_memberships = relationship("FacultyUploadBatchMember", back_populates="faculty", cascade="all, delete-orphan")

class FacultyUploadBatch(Base):
    __tablename__ = "faculty_upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String(150), default="Uploaded Faculty Batch", nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    total_extracted = Column(Integer, default=0, nullable=False)
    matched_existing_count = Column(Integer, default=0, nullable=False)
    new_added_count = Column(Integer, default=0, nullable=False)
    eligible_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False) # Marked as latest active batch
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    members = relationship("FacultyUploadBatchMember", back_populates="batch", cascade="all, delete-orphan")

class FacultyUploadBatchMember(Base):
    __tablename__ = "faculty_upload_batch_members"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("faculty_upload_batches.id", ondelete="CASCADE"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    is_eligible = Column(Boolean, default=True, nullable=False)
    notes = Column(String(255), nullable=True)

    batch = relationship("FacultyUploadBatch", back_populates="members")
    faculty = relationship("Faculty", back_populates="batch_memberships")
