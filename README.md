# Smart Exam Duty Fairness & Allocation System (Kam Bato Algo)

A production-ready, centralized, transparent, and mathematically fair examination duty allocation web application built for engineering college examination departments.

Designed to allocate examination duties across **300+ faculty members** from **12 departments** without department-level favoritism, discretion, or workload imbalance.

---

## 1. Problem Statement & Core Objective

Currently in many engineering institutions, examination duty charts are prepared at a high level, but the actual critical roles (**Junior Supervisor**, **Reliever**, or **Standby**) are assigned later by individual Department Senior Supervisors.

This discretionary assignment introduces severe fairness disparities:
- Certain junior or non-favored faculty members repeatedly receive stressful **Junior Supervisor (JS)** classroom duties.
- Other faculty members repeatedly receive lighter **Reliever** or reserve **Standby** duties.
- Department-level discretion enables favoritism and uneven distribution.

**The Solution:**
The **Smart Exam Duty Fairness & Allocation System** completely eliminates department discretion by enforcing a single, centralized, mathematically proven fairness optimization algorithm across all 12 academic departments.

---

## 2. Duty Categories & System Rules

| Duty Role | Description | Allocation Rule |
| :--- | :--- | :--- |
| **Junior Supervisor (JS)** | Classroom invigilation inside examination blocks. | Exactly 1 JS per classroom block. Calculated directly from available examination rooms. |
| **Reliever** | Temporarily relieves Junior Supervisors (e.g. 10 mins after every hour). | Allocated based on configured coverage ratio (default: 1 Reliever per 4 classrooms). |
| **Standby** | Reserve personnel stationed at Examination Control for emergency replacements. | Distributed evenly among remaining eligible faculty. |
| **Senior Supervisor (SS)** | Assigned to Heads of Department (HOD) and Deputy HODs. | Tracked separately for institutional reporting. Excluded from JS/Reliever/Standby fairness pool by policy. |

> **Note:** As specified in institutional requirements, no **IS** (Internal Supervisor) duty category exists in this system.

---

## 3. Algorithmic Fairness Architecture (Google OR-Tools CP-SAT)

The allocation engine is powered by **Google OR-Tools CP-SAT (Constraint Programming - Satisfiability)** solver.

### Decision Variables
For each eligible faculty $i \in \{1, \dots, N\}$:
- $x_{i, JS} \in \{0, 1\}$
- $x_{i, Rel} \in \{0, 1\}$
- $x_{i, Stb} \in \{0, 1\}$

### Hard Constraints
1. **Single Duty per Faculty per Shift:**
   $$\forall i: \quad x_{i, JS} + x_{i, Rel} + x_{i, Stb} = 1$$
2. **Exact Classroom Block Matching:**
   $$\sum_{i=1}^N x_{i, JS} = K_{JS} \quad (\text{where } K_{JS} = \text{number of examination blocks})$$
3. **Exact Reliever Coverage:**
   $$\sum_{i=1}^N x_{i, Rel} = K_{Rel} \quad (\text{where } K_{Rel} = \lceil K_{JS} / \text{ratio} \rceil)$$
4. **Exact Standby Reserves:**
   $$\sum_{i=1}^N x_{i, Stb} = N - K_{JS} - K_{Rel}$$
5. **Department Equity Bounds:**
   For any department $d$ with $N_d$ faculty:
   $$\lfloor \frac{N_d}{N} \cdot K_{JS} \rfloor - 1 \le \sum_{i \in \text{dept } d} x_{i, JS} \le \lceil \frac{N_d}{N} \cdot K_{JS} \rceil + 1$$
   *(Guarantees no department is over-burdened or favored).*

### Multi-Objective Cost Function
$$\min \sum_{i=1}^N \Big( \text{Cost}(i, JS) \cdot x_{i, JS} + \text{Cost}(i, Rel) \cdot x_{i, Rel} + \text{Cost}(i, Stb) \cdot x_{i, Stb} \Big)$$

- **JS Penalty:** Scaled by $W_{JS} \cdot (JS_i - \overline{JS}) + W_{Consec} \cdot \text{Consecutive}_i$.
- **Reliever Incentive:** Scaled by $W_{Rel} \cdot (Rel_i - \overline{Rel}) - (W_{JS} \cdot 0.8) \cdot (JS_i - \overline{JS})$.
- **Standby Incentive:** Scaled by $W_{Stb} \cdot (Stb_i - \overline{Stb}) - (W_{JS} \cdot 0.9) \cdot (JS_i - \overline{JS})$.

### Explainable AI Output
For every single faculty member, the solver generates an automated, human-readable reason, such as:
> *"Assigned Reliever because faculty has served disproportionately high JS duties (8 vs avg 4.8) and lower Reliever duties (0). Workload equity compensation applied."*

---

## 4. Technology Stack

- **Backend:** Python 3.10 / 3.13 / 3.14, FastAPI, SQLAlchemy ORM, Pydantic v2
- **Fairness Solver:** Google OR-Tools CP-SAT (Integer & Constraint Programming)
- **Database:** SQLite (default zero-friction embedded) / PostgreSQL (production connection ready via `DATABASE_URL`)
- **Document & OCR Parsing:** Pandas, OpenPyXL, python-docx, pypdf, Pillow, Tesseract OCR
- **Reporting Engine:** ReportLab (vector PDF generation), OpenPyXL (formatted Excel generation)
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts, Lucide Icons
- **Security:** JWT authentication, bcrypt password hashing, role-based authorization, comprehensive audit logs

---

## 5. Official Staff Master (Staff List - 02.09.2026.xls)

The application has been directly populated with the official institutional staff roster:
- **Total Registered Faculty:** 368 faculty members
- **Total Academic Departments:** 18 departments
- **Exact Titles & Names:** Extracted and normalized (e.g. `Dr. B. K. Mishra`, `Dr. Lochan Jolly`, `Dr. Vinitkumar Dongre`, `Dr. Payel Saha`, `Dr. Sanjeev Chaudhari`, `Prof. Sonia Behra`, etc.)
- **Exact Positions & Designations:** Preserved exactly from institutional records (e.g. `Principal`, `Dean-Student & Staff (Welfare),Professor`, `Dean (R&D),Professor`, `HOD,Professor`, `Associate Professor`, `Assistant Professor`, `Professor; Controller of Examination`, etc.)
- **Official Date of Joining (DOJ):** Extracted and converted to canonical date records.

---

## 6. System Modules & Screens

The application implements all 12 modules accessible via the left sidebar:

1. **Dashboard (`/`):**
   - KPI counters: Total Faculty (310), Departments (12), Available Blocks (32), Total JS, Relievers, Standby.
   - Gini equity coefficient (0.167 - high equity).
   - Interactive charts: Department-wise duty distribution, Role composition ratio.
   - Candidates of interest: Faculty with highest JS count, lowest Reliever count, lowest Standby count.
2. **Faculty Management (`/faculty`):**
   - 310 pre-seeded faculty records across 12 departments.
   - Real-time search by name, ID, and designation.
   - Department and role filtering.
   - Add/Edit/Delete faculty modals with validation.
   - Excel Import and Export.
3. **Department Management (`/departments`):**
   - 12 Academic departments (CSE, IT, AIDS, EXTC, ELEC, MECH, CIVIL, CHEM, BIOTECH, APPMATH, HUMSCI, INST).
   - HOD details, faculty headcount, and department-level equity statistics.
4. **Examination Management (`/examinations`):**
   - Examination levels (Second Year, etc.), academic years, dates, and shifts (Morning, Afternoon, Evening).
   - Configurable classroom block capacities and room lists (e.g. R-101 to R-132).
5. **Upload Duty Chart (`/upload`):**
   - Multi-format ingestion: Excel (`.xlsx`, `.xls`), Word (`.docx`), PDF (`.pdf`), and Scanned Images (`.png`, `.jpg`).
   - Fuzzy matching with match confidence score (0-100%).
   - Interactive **Verification Screen** allowing administrators to correct recognized names or duty roles before saving into history.
6. **Automatic & Next Day Allocation (`/allocation`):**
   - Examination date and shift selection.
   - Automatic room block detection with explicit missing block prompt.
   - Configurable reliever coverage ratio (1:4 default).
   - Generates allocation table with faculty name, department, past duty counters, proposed duty, assigned room/group, and **Explainability Reason**.
   - Manual role override modal with mandatory justification.
   - **Approve & Publish Allocation** button.
   - **Export Excel** and **Export PDF** buttons.
7. **Faculty Duty History (`/history`):**
   - Permanent date-wise historical duty records. Historical records are never overwritten.
8. **Fairness Analytics (`/analytics`):**
   - Gini equity index, department bias detector, duty distribution curves.
9. **Official Reports (`/reports`):**
   - 8 Mandatory Institutional Reports:
     1. Daily Duty Allocation Report
     2. Faculty-wise Duty History
     3. Department-wise Duty Report
     4. JS Distribution Report
     5. Reliever Distribution Report
     6. Standby Distribution Report
     7. Fairness Analysis Report
     8. Manual Modification & Audit Report
   - Export to **Excel (.xlsx)**, **PDF (.pdf)**, and **Printable HTML**.
10. **User Management & Audit Logs (`/users`):**
    - Role management (Super Admin, Examination Controller, Department HOD, Faculty).
    - Chronological audit log of manual overrides and approvals with timestamps.
11. **Settings (`/settings`):**
    - Configurable solver weights ($W_{JS}$, $W_{Rel}$, $W_{Stb}$, $W_{Consecutive}$, $W_{Dept}$).
    - Reliever ratio selector.
    - HOD Senior Supervisor exclusion toggle.

---

## 6. Testing & Validation Scenarios

The test suite in `backend/tests/test_allocation.py` verifies all 6 mandatory scenarios:

- **Scenario 1:** 50 eligible faculty and 32 examination blocks $\rightarrow$ 32 JS, 8 Relievers, 10 Standby.
- **Scenario 2:** 60 eligible faculty and 32 examination blocks $\rightarrow$ 32 JS, 8 Relievers, 20 Standby.
- **Scenario 3:** Faculty with repeatedly high JS history receives mathematical priority for Reliever or Standby relief.
- **Scenario 4:** Departments of unequal size (e.g. 15 vs 5 faculty) are held to the exact same proportional equity policy without favoritism.
- **Scenario 5:** Uploaded files with missing block count prompt the Examination Controller instead of guessing room numbers.
- **Scenario 6:** Duplicate entries within the same shift are prevented.

Run the test suite:
```bash
.\venv\Scripts\pytest.exe backend\tests\test_allocation.py -v
```

---

## 7. Installation & Quick Start

### Prerequisites
- Python 3.10+ (or Python 3.13)
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# In project root
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic ortools pandas openpyxl python-docx pypdf pillow reportlab python-multipart pyjwt bcrypt pytest email-validator

# Run database migration & initial seed (310 faculty, 12 depts)
$env:PYTHONPATH="backend"
python -c "from app.core.database import Base, engine, SessionLocal; from app.services.seed_data import seed_database; Base.metadata.create_all(bind=engine); db = SessionLocal(); seed_database(db); db.close()"

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run build
npm run start -p 3000
```

Open your browser to:
- Frontend: **`http://localhost:3000`**
- Backend Interactive API Docs: **`http://127.0.0.1:8000/docs`**

### Default User Credentials
| Username | Password | Role | Scope |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | **Super Admin** | Full application & system control |
| `controller` | `controller123` | **Examination Controller** | Upload duty charts, run & approve allocations |
| `hod_cse` | `hod123` | **Department HOD** | View CSE department faculty allocations |
