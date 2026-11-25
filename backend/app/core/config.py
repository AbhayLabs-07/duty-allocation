import os
import shutil
from pydantic import BaseModel
from typing import Optional

IS_VERCEL = bool(os.getenv("VERCEL"))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if IS_VERCEL:
    # Vercel serverless functions have a read-only root filesystem.
    # Copy the seeded database to /tmp so writes/allocations succeed.
    tmp_db_path = "/tmp/kam_bato.db"
    possible_sources = [
        os.path.join(ROOT_DIR, "kam_bato.db"),
        os.path.join(os.path.dirname(ROOT_DIR), "kam_bato.db"),
        os.path.join(os.getcwd(), "kam_bato.db"),
    ]
    if not os.path.exists(tmp_db_path):
        for src in possible_sources:
            if os.path.exists(src):
                try:
                    shutil.copyfile(src, tmp_db_path)
                    break
                except Exception:
                    pass
    default_db_url = f"sqlite:///{tmp_db_path}" if os.path.exists(tmp_db_path) else "sqlite:///./kam_bato.db"
    default_upload_dir = "/tmp/uploads"
else:
    default_db_url = "sqlite:///./kam_bato.db"
    default_upload_dir = os.path.join(ROOT_DIR, "uploads")

class Settings(BaseModel):
    PROJECT_NAME: str = "Smart Exam Duty Fairness & Allocation System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database: Supports SQLite by default or PostgreSQL via environment variable
    DATABASE_URL: str = os.getenv("DATABASE_URL", default_db_url)
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "kam-bato-algo-super-secret-key-exam-fairness-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Upload folder
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", default_upload_dir)
    
    # Algorithm Default Configuration
    DEFAULT_RELIEVER_RATIO: int = 4  # 1 Reliever per 4 examination blocks
    WEIGHT_PREV_JS: float = 2.5      # Penalty weight for assigning JS to someone with high JS history
    WEIGHT_PREV_RELIEVER: float = 2.0 # Incentive for assigning Reliever to someone with low Reliever history
    WEIGHT_PREV_STANDBY: float = 1.5  # Incentive for assigning Standby to someone with low Standby history
    WEIGHT_CONSECUTIVE: float = 2.0   # Penalty for consecutive day duties
    WEIGHT_DEPT_EQUITY: float = 1.5   # Weight ensuring all departments have balanced distribution

settings = Settings()

try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception:
    pass
