import os
import sys

# Integrate exact staff list loader as primary seed
from scripts.load_real_staff import populate_exact_staff, extract_faculty_from_excel

def seed_database(db):
    from app.models.faculty import Faculty
    # If already loaded with real staff (>= 350 faculty), skip
    if db.query(Faculty).count() >= 350:
        return
    print("Seeding database using exact records from 'Staff List - 02.09.2026.xls'...")
    populate_exact_staff()
