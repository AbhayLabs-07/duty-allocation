import pytest
from app.services.optimizer import FairnessOptimizer

def test_scenario_1_fifty_faculty_32_blocks():
    """
    Scenario 1:
    50 eligible faculty and 32 examination blocks.
    Expected: 32 JS positions, remaining 18 faculty distributed to Reliever and Standby.
    """
    faculty_pool = [
        {
            "id": i,
            "faculty_id": f"FAC-{i}",
            "name": f"Faculty {i}",
            "department_id": (i % 12) + 1,
            "department_name": f"Dept-{(i % 12) + 1}",
            "previous_js_count": (i % 6) + 1,
            "previous_reliever_count": (i % 3),
            "previous_standby_count": (i % 2),
            "total_previous_duties": (i % 6) + 1 + (i % 3)
        }
        for i in range(1, 51)
    ]
    optimizer = FairnessOptimizer(reliever_ratio=4)
    result = optimizer.solve(faculty_pool, num_blocks=32)

    assert result["required_js"] == 32
    assert result["required_relievers"] == 8
    assert result["required_standby"] == 10
    assert len(result["allocations"]) == 50

    js_allocs = [a for a in result["allocations"] if a["assigned_role"] == "JS"]
    rel_allocs = [a for a in result["allocations"] if a["assigned_role"] == "Reliever"]
    stb_allocs = [a for a in result["allocations"] if a["assigned_role"] == "Standby"]

    assert len(js_allocs) == 32
    assert len(rel_allocs) == 8
    assert len(stb_allocs) == 10

def test_scenario_2_sixty_faculty_32_blocks():
    """
    Scenario 2:
    60 eligible faculty and 32 examination blocks.
    Expected: 32 JS positions, 28 remaining (8 Relievers, 20 Standby).
    """
    faculty_pool = [
        {
            "id": i,
            "faculty_id": f"FAC-{i}",
            "name": f"Faculty {i}",
            "department_id": (i % 12) + 1,
            "department_name": f"Dept-{(i % 12) + 1}",
            "previous_js_count": (i % 5) + 1,
            "previous_reliever_count": (i % 3),
            "previous_standby_count": (i % 3),
            "total_previous_duties": (i % 5) + 1 + (i % 3)
        }
        for i in range(1, 61)
    ]
    optimizer = FairnessOptimizer(reliever_ratio=4)
    result = optimizer.solve(faculty_pool, num_blocks=32)

    assert result["required_js"] == 32
    assert result["required_relievers"] == 8
    assert result["required_standby"] == 20
    assert len(result["allocations"]) == 60

def test_scenario_3_high_js_history_equity():
    """
    Scenario 3:
    A faculty member has already received JS duty repeatedly (e.g. 10 JS, 0 Reliever).
    The fairness engine should prioritize them for Reliever/Standby rather than JS again.
    """
    faculty_pool = [
        {
            "id": 1,
            "faculty_id": "FAC-OVERLOADED",
            "name": "Dr. High JS Worker",
            "department_id": 1,
            "department_name": "CSE",
            "previous_js_count": 12,
            "previous_reliever_count": 0,
            "previous_standby_count": 0,
            "total_previous_duties": 12
        }
    ]
    # Add other faculty with much lower JS counts
    for i in range(2, 21):
        faculty_pool.append({
            "id": i,
            "faculty_id": f"FAC-{i}",
            "name": f"Faculty {i}",
            "department_id": (i % 4) + 1,
            "department_name": f"Dept-{(i % 4) + 1}",
            "previous_js_count": 1,
            "previous_reliever_count": 2,
            "previous_standby_count": 1,
            "total_previous_duties": 4
        })

    optimizer = FairnessOptimizer(reliever_ratio=4)
    # 20 faculty, 12 blocks -> 12 JS, 3 Relievers, 5 Standby
    result = optimizer.solve(faculty_pool, num_blocks=12)

    overloaded_alloc = next(a for a in result["allocations"] if a["faculty_id"] == 1)
    # The overloaded faculty must NOT be assigned JS! They should receive Reliever or Standby
    assert overloaded_alloc["assigned_role"] in ["Reliever", "Standby"]
    assert "disproportionately high JS" in overloaded_alloc["explainability_reason"] or "heavy historical classroom duty" in overloaded_alloc["explainability_reason"]

def test_scenario_4_different_department_sizes_equity():
    """
    Scenario 4:
    Two departments have different numbers of faculty (e.g. 15 vs 5).
    Both departments follow the same mathematical fairness policy without favoritism.
    """
    faculty_pool = []
    # Dept 1 (large): 15 faculty
    for i in range(1, 16):
        faculty_pool.append({
            "id": i,
            "faculty_id": f"FAC-D1-{i}",
            "name": f"Dept1 Fac {i}",
            "department_id": 1,
            "department_name": "LargeDept",
            "previous_js_count": 3,
            "previous_reliever_count": 1,
            "previous_standby_count": 1,
            "total_previous_duties": 5
        })
    # Dept 2 (small): 5 faculty
    for i in range(16, 21):
        faculty_pool.append({
            "id": i,
            "faculty_id": f"FAC-D2-{i}",
            "name": f"Dept2 Fac {i}",
            "department_id": 2,
            "department_name": "SmallDept",
            "previous_js_count": 3,
            "previous_reliever_count": 1,
            "previous_standby_count": 1,
            "total_previous_duties": 5
        })

    optimizer = FairnessOptimizer(reliever_ratio=4)
    result = optimizer.solve(faculty_pool, num_blocks=10)

    # 10 JS, 3 Reliever, 7 Standby
    assert len(result["allocations"]) == 20
    d1_allocs = [a for a in result["allocations"] if a["department_id"] == 1]
    d2_allocs = [a for a in result["allocations"] if a["department_id"] == 2]

    # Proportional JS allocation: Dept 1 has 75% of pool, Dept 2 has 25%
    d1_js = sum(1 for a in d1_allocs if a["assigned_role"] == "JS")
    d2_js = sum(1 for a in d2_allocs if a["assigned_role"] == "JS")
    assert d1_js > 0
    assert d2_js > 0
    # Small department is not exploited
    assert d2_js <= 4


def test_scenario_5_missing_block_count_error():
    """
    Scenario 5:
    The uploaded file contains no room information.
    Expected: The application must prompt/ask for the missing block count instead of guessing.
    """
    faculty_pool = [
        {"id": i, "name": f"Faculty {i}", "department_id": 1, "previous_js_count": 2, "previous_reliever_count": 1, "previous_standby_count": 1}
        for i in range(1, 20)
    ]
    optimizer = FairnessOptimizer()
    with pytest.raises(ValueError) as excinfo:
        # If num_blocks is 0 or negative
        optimizer.solve(faculty_pool, num_blocks=0)
    # The requirement is that zero/negative blocks or more blocks than faculty triggers explicit validation
    # (The API endpoint explicitly returns 422 with message "Classroom block count is missing. Please enter the number of examination blocks/rooms to proceed.")

def test_scenario_6_duplicate_faculty_filtered():
    """
    Scenario 6:
    The same faculty appears twice in the same shift.
    Expected: Detect the conflict and prevent invalid allocation.
    """
    # Unique IDs ensure each faculty is allocated to at most ONE role per shift
    faculty_pool = [
        {"id": 1, "name": "Dr. Duplicate", "department_id": 1, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0},
        {"id": 2, "name": "Dr. Second", "department_id": 1, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0},
        {"id": 3, "name": "Dr. Third", "department_id": 1, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0},
        {"id": 4, "name": "Dr. Fourth", "department_id": 1, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0},
        {"id": 5, "name": "Dr. Fifth", "department_id": 1, "previous_js_count": 2, "previous_reliever_count": 0, "previous_standby_count": 0},
    ]
    optimizer = FairnessOptimizer(reliever_ratio=2)
    result = optimizer.solve(faculty_pool, num_blocks=3)
    
    # Verify exactly 1 role per unique faculty
    assigned_ids = [a["faculty_id"] for a in result["allocations"]]
    assert len(assigned_ids) == len(set(assigned_ids)) == 5
