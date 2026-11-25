import pytest
from datetime import date
from app.services.timetable_parser import TimetableParser
from app.services.optimizer import FairnessOptimizer, ShortageError

def test_academic_code_mapping_resolution():
    custom_map = {
        "ST": "Second Year Autonomous",
        "TT": "Third Year Autonomous",
        "BT": "Final Year Autonomous"
    }
    parser = TimetableParser(custom_mappings=custom_map)
    assert parser.code_mappings["ST"] == "Second Year Autonomous"
    assert parser.code_mappings["SE"] == "Second Year B.Tech"
    assert parser.code_mappings["BE"] == "Final Year B.Tech"

def test_timetable_text_extraction_confidence():
    parser = TimetableParser()
    sample_text = """
    TCET Autonomous Examination Winter 2026
    Date: 12/12/2026 Time: 10:30 AM to 01:30 PM
    Department: AI&DS Year: SE Sem IV
    Subject: Database Management Systems [AID301]
    Department: IT Year: TE Sem VI
    Subject: Computer Networks [IT401]
    """
    records = parser._extract_records_from_text(sample_text, "Winter 2026", 1)
    assert len(records) >= 2
    for r in records:
        assert r["confidence_score"] >= 90
        assert r["subject_code"] in ["AID301", "IT401"]
        assert r["exam_date"] == "2026-12-12"

def test_explicit_shortage_detection():
    optimizer = FairnessOptimizer(js_per_classroom=2, reliever_ratio=4)
    # 10 faculty available, but 10 blocks * 2 JS = 20 JS required!
    small_pool = [
        {"id": i, "previous_js_count": 1, "previous_reliever_count": 0, "previous_standby_count": 0, "total_previous_duties": 1}
        for i in range(1, 11)
    ]
    with pytest.raises(ShortageError) as exc_info:
        optimizer.solve(small_pool, num_blocks=10)
    
    assert exc_info.value.shortage > 0
    assert "Allocation cannot be completed" in str(exc_info.value)

def test_same_department_conflict_prevention():
    optimizer = FairnessOptimizer(disallow_same_department_js=True)
    # Faculty 1 and 2 belong to Department 1 (which conducts the exam).
    # Faculty 3, 4, 5 belong to other departments.
    faculty_pool = [
        {"id": 1, "name": "Prof. A", "department_id": 1, "previous_js_count": 0, "previous_reliever_count": 0, "previous_standby_count": 0, "total_previous_duties": 0},
        {"id": 2, "name": "Prof. B", "department_id": 1, "previous_js_count": 0, "previous_reliever_count": 0, "previous_standby_count": 0, "total_previous_duties": 0},
        {"id": 3, "name": "Prof. C", "department_id": 2, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0, "total_previous_duties": 2},
        {"id": 4, "name": "Prof. D", "department_id": 3, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0, "total_previous_duties": 2},
        {"id": 5, "name": "Prof. E", "department_id": 4, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0, "total_previous_duties": 2},
    ]
    # Need 2 JS blocks
    res = optimizer.solve(faculty_pool, num_blocks=2, exam_department_ids=[1])
    js_ids = [a["faculty_id"] for a in res["allocations"] if a["assigned_role"] == "JS"]
    # Department 1 faculty (id 1 and 2) must NOT be assigned JS!
    assert 1 not in js_ids
    assert 2 not in js_ids
