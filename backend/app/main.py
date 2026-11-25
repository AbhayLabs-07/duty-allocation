from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.services.seed_data import seed_database

# Import routers
from app.api.auth import router as auth_router
from app.api.faculty import router as faculty_router
from app.api.departments import router as departments_router
from app.api.examinations import router as examinations_router
from app.api.timetables import router as timetables_router
from app.api.documents import router as documents_router
from app.api.allocation import router as allocation_router
from app.api.history import router as history_router
from app.api.analytics import router as analytics_router
from app.api.reports import router as reports_router
from app.api.users import router as users_router
from app.api.settings import router as settings_router
from app.api.rules import router as rules_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Centralized, Transparent & Fair Examination Duty Allocation System for Engineering Colleges",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(timetables_router, prefix="/api/timetables", tags=["Timetable & OCR Processing"])
app.include_router(faculty_router, prefix="/api/faculty", tags=["Faculty Master & Availability"])
app.include_router(departments_router, prefix="/api/departments", tags=["Department Management"])
app.include_router(examinations_router, prefix="/api/examinations", tags=["Examination Management"])
app.include_router(documents_router, prefix="/api/documents", tags=["Duty Chart Processing"])
app.include_router(allocation_router, prefix="/api/allocation", tags=["Fairness Allocation Engine"])
app.include_router(rules_router, prefix="/api/rules", tags=["System & Conflict Rules"])
app.include_router(history_router, prefix="/api/history", tags=["Duty History"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Fairness Analytics & Dashboard"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports & Exports"])
app.include_router(users_router, prefix="/api/users", tags=["User & Audit Management"])
app.include_router(settings_router, prefix="/api/settings", tags=["System Configuration"])

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "Operational",
        "docs": "/docs"
    }
