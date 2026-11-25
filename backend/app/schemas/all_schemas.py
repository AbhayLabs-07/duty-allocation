from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    department_id: Optional[int] = None
    faculty_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Department ---
class DepartmentBase(BaseModel):
    code: str
    name: str
    hod_name: Optional[str] = None
    contact_email: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    hod_name: Optional[str] = None
    contact_email: Optional[str] = None

class DepartmentOut(DepartmentBase):
    id: int
    faculty_count: Optional[int] = 0
    class Config:
        from_attributes = True

# --- Faculty ---
class FacultyBase(BaseModel):
    faculty_id: str
    name: str
    department_id: int
    designation: str # Professor, Associate Professor, Assistant Professor
    role_category: str = "Faculty" # HOD, Dy. HOD, Faculty
    employment_status: str = "Regular"
    eligibility: bool = True
    joining_date: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class FacultyCreate(FacultyBase):
    previous_js_count: Optional[int] = 0
    previous_reliever_count: Optional[int] = 0
    previous_standby_count: Optional[int] = 0
    previous_ss_count: Optional[int] = 0

class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    designation: Optional[str] = None
    role_category: Optional[str] = None
    employment_status: Optional[str] = None
    eligibility: Optional[bool] = None
    joining_date: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    previous_js_count: Optional[int] = None
    previous_reliever_count: Optional[int] = None
    previous_standby_count: Optional[int] = None
    previous_ss_count: Optional[int] = None

class FacultyOut(FacultyBase):
    id: int
    department_name: Optional[str] = None
    total_previous_duties: int = 0
    previous_js_count: int = 0
    previous_reliever_count: int = 0
    previous_standby_count: int = 0
    previous_ss_count: int = 0
    class Config:
        from_attributes = True

# --- Examination ---
class ExamRoomCreate(BaseModel):
    block_number: int
    room_number: str
    block_label: Optional[str] = None
    capacity: int = 30
    floor: Optional[str] = None
    building: Optional[str] = None

class ExamRoomOut(ExamRoomCreate):
    id: int
    shift_id: int
    class Config:
        from_attributes = True

class ExamShiftCreate(BaseModel):
    shift_name: str # Morning, Afternoon, Evening
    start_time: Optional[str] = "10:00 AM"
    end_time: Optional[str] = "01:00 PM"
    block_count: int = 0
    room_list_str: Optional[str] = None
    rooms: List[ExamRoomCreate] = []

class ExamShiftOut(BaseModel):
    id: int
    exam_date_id: int
    shift_name: str
    start_time: Optional[str]
    end_time: Optional[str]
    block_count: int
    room_list_str: Optional[str]
    status: str
    rooms: List[ExamRoomOut] = []
    class Config:
        from_attributes = True

# Aliases for backward compatibility
ShiftOut = ExamShiftOut
RoomCreate = ExamRoomCreate
RoomOut = ExamRoomOut

class ExamDateCreate(BaseModel):
    exam_date: date
    day_name: Optional[str] = None
    shifts: List[ExamShiftCreate] = []

class ExamDateOut(BaseModel):
    id: int
    exam_id: int
    exam_date: date
    day_name: Optional[str]
    shifts: List[ExamShiftOut] = []
    class Config:
        from_attributes = True

class ExaminationCreate(BaseModel):
    name: str
    academic_year: str
    semester: str
    exam_level: str = "Second Year"
    start_date: date
    end_date: date
    dates: List[ExamDateCreate] = []

class ExaminationOut(BaseModel):
    id: int
    name: str
    academic_year: str
    semester: str
    exam_level: str
    start_date: date
    end_date: date
    is_active: bool
    dates: List[ExamDateOut] = []
    class Config:
        from_attributes = True

# --- Duty Chart Upload & Extraction ---
class ExtractedRecordUpdate(BaseModel):
    id: int
    matched_faculty_id: Optional[int] = None
    verified_duty_role: Optional[str] = None
    is_verified: bool = True
    verification_notes: Optional[str] = None

class ExtractedRecordOut(BaseModel):
    id: int
    upload_id: int
    raw_faculty_name: str
    raw_department: Optional[str] = None
    raw_date: Optional[str] = None
    raw_shift: Optional[str] = None
    raw_duty_role: Optional[str] = None
    raw_total_duty: Optional[int] = None
    matched_faculty_id: Optional[int] = None
    matched_faculty_name: Optional[str] = None
    matched_department_id: Optional[int] = None
    verified_duty_role: Optional[str] = None
    confidence_score: int
    is_verified: bool
    verification_notes: Optional[str] = None
    class Config:
        from_attributes = True

class UploadedChartOut(BaseModel):
    id: int
    filename: str
    file_type: str
    uploaded_at: datetime
    status: str
    total_records_extracted: int
    detected_exam_name: Optional[str] = None
    detected_exam_year: Optional[str] = None
    detected_semester: Optional[str] = None
    detected_exam_date: Optional[date] = None
    detected_shift: Optional[str] = None
    detected_block_count: Optional[int] = None
    detected_rooms: Optional[str] = None
    extracted_records: List[ExtractedRecordOut] = []
    class Config:
        from_attributes = True

# --- Allocation ---
class AllocationRunRequest(BaseModel):
    shift_id: int
    batch_id: Optional[int] = None # Restrict strictly to this uploaded faculty batch
    block_count: Optional[int] = None  # Classrooms being used
    js_per_classroom: Optional[int] = 1 # Supervisors per classroom (e.g. 1 or 2)
    reliever_ratio: Optional[int] = None # e.g. 4
    reliever_count: Optional[int] = None # Or exact requested count
    standby_count: Optional[int] = None # Configurable standby count
    disallow_same_department_js: Optional[bool] = False
    department_filter: Optional[List[int]] = None
    faculty_ids: Optional[List[int]] = None
    recalculate: bool = False

class DutyAllocationOut(BaseModel):
    id: int
    shift_id: int
    faculty_id: int
    faculty_name: str
    department_name: str
    designation: Optional[str] = "Assistant Professor"
    assigned_role: str # 'JS', 'Reliever', 'Standby', 'SS'
    assigned_block: Optional[str] = None
    status: str
    fairness_score: float
    prev_js_snapshot: int
    prev_reliever_snapshot: int
    prev_standby_snapshot: int
    prev_total_snapshot: int
    previous_role: Optional[str] = "JS"
    explainability_reason: str
    is_manual_override: bool
    original_role: Optional[str] = None
    override_reason: Optional[str] = None
    override_by_user: Optional[str] = None
    class Config:
        from_attributes = True

class AllocationSummary(BaseModel):
    shift_id: int
    exam_name: str
    exam_date: str
    shift_name: str
    total_eligible_faculty: int
    required_js: int
    required_relievers: int
    required_standby: int
    required_ss: int = 0
    overall_fairness_score: Optional[float] = 95.0
    shortage: Optional[int] = 0
    allocations: List[DutyAllocationOut]
    solver_status: str
    execution_time_seconds: float
    fairness_variance_score: float

class ManualOverrideRequest(BaseModel):
    allocation_id: int
    new_role: str
    new_block: Optional[str] = None
    override_reason: str

class ImpactCheckRequest(BaseModel):
    shift_id: int
    original_faculty_id: int
    replacement_faculty_id: int
    new_role: str

class ReplaceFacultyRequest(BaseModel):
    allocation_id: int
    replacement_faculty_id: int
    new_role: Optional[str] = None
    override_reason: str
    performed_by: Optional[str] = "Controller of Examination"

class RequirementCalculationRequest(BaseModel):
    num_classrooms: int
    batch_id: Optional[int] = None # Restrict strictly to this uploaded faculty batch
    js_per_classroom: int = 1
    reliever_ratio: int = 4
    standby_count: Optional[int] = None

# --- Configuration & Settings ---
class ConfigurationOut(BaseModel):
    id: int
    name: str
    reliever_ratio: int
    js_per_classroom: int = 1
    disallow_same_department_js: bool = False
    disallow_same_subject_js: bool = False
    weight_prev_js: float
    weight_prev_reliever: float
    weight_prev_standby: float
    weight_consecutive: float
    weight_dept_equity: float
    exclude_ss_from_fairness: bool
    is_active: bool
    class Config:
        from_attributes = True

class ConfigurationUpdate(BaseModel):
    reliever_ratio: Optional[int] = None
    js_per_classroom: Optional[int] = None
    disallow_same_department_js: Optional[bool] = None
    disallow_same_subject_js: Optional[bool] = None
    weight_prev_js: Optional[float] = None
    weight_prev_reliever: Optional[float] = None
    weight_prev_standby: Optional[float] = None
    weight_consecutive: Optional[float] = None
    weight_dept_equity: Optional[float] = None
    exclude_ss_from_fairness: Optional[bool] = None

# --- History ---
class DutyHistoryOut(BaseModel):
    id: int
    faculty_id: int
    faculty_name: str
    department_name: str
    exam_name: str
    academic_year: Optional[str]
    semester: Optional[str]
    exam_date: date
    shift_name: str
    role_served: str
    block_or_room: Optional[str]
    is_manual_override: bool
    recorded_at: datetime
    class Config:
        from_attributes = True

# --- Analytics / Dashboard ---
class DashboardSummary(BaseModel):
    total_faculty: int
    total_departments: int
    upcoming_examinations: int
    available_blocks: int
    total_js_assigned: int
    total_reliever_assigned: int
    total_standby_assigned: int
    total_ss_assigned: int
    fairness_gini_coefficient: float
    faculty_highest_js: List[Dict[str, Any]]
    faculty_lowest_reliever: List[Dict[str, Any]]
    faculty_lowest_standby: List[Dict[str, Any]]
    department_distribution: List[Dict[str, Any]]
    recent_allocations: List[Dict[str, Any]]
