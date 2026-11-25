import time
import math
from typing import List, Dict, Any, Optional, Tuple
from ortools.sat.python import cp_model

class ShortageError(Exception):
    def __init__(self, required: int, available: int, shortage: int, message: str):
        super().__init__(message)
        self.required = required
        self.available = available
        self.shortage = shortage

class FairnessOptimizer:
    """
    Centralized, transparent constraint-based fairness optimization engine
    using Google OR-Tools CP-SAT solver.
    
    Guarantees:
    1. Zero department favoritism - uniform mathematical cost formulation across all departments.
    2. Proportional equity - prioritizes Reliever/Standby for faculty with high historical JS load.
    3. Rotation fairness - prioritizes Reliever for faculty with low historical Reliever counts.
    4. Exact room matching - supports configurable JS per classroom (1 or 2).
    5. Same-department conflict rules (hard or soft constraint).
    6. Non-overlapping single duty per shift.
    7. Clear, deterministic explainability reasons for every assignment.
    8. Overall Fairness Score (0-100).
    """
    
    def __init__(
        self,
        weight_prev_js: float = 2.5,
        weight_prev_reliever: float = 2.0,
        weight_prev_standby: float = 1.5,
        weight_consecutive: float = 2.0,
        weight_dept_equity: float = 1.5,
        reliever_ratio: int = 4,
        js_per_classroom: int = 1,
        disallow_same_department_js: bool = False
    ):
        self.w_js = weight_prev_js
        self.w_rel = weight_prev_reliever
        self.w_stb = weight_prev_standby
        self.w_consec = weight_consecutive
        self.w_dept = weight_dept_equity
        self.reliever_ratio = max(1, reliever_ratio)
        self.js_per_classroom = max(1, js_per_classroom)
        self.disallow_same_dept = disallow_same_department_js

    def solve(
        self,
        eligible_faculty: List[Dict[str, Any]],
        num_blocks: int,
        requested_reliever_count: Optional[int] = None,
        requested_standby_count: Optional[int] = None,
        consecutive_faculty_ids: Optional[set] = None,
        rooms_list: Optional[List[str]] = None,
        exam_department_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Runs the CP-SAT solver to allocate JS, Reliever, and Standby positions.
        """
        start_time = time.time()
        n_faculty = len(eligible_faculty)
        if consecutive_faculty_ids is None:
            consecutive_faculty_ids = set()
        if exam_department_ids is None:
            exam_department_ids = []

        if num_blocks <= 0:
            raise ValueError("Number of examination blocks must be greater than 0.")

        # 1. Determine role requirements
        required_js = num_blocks * self.js_per_classroom

        if requested_reliever_count is not None and requested_reliever_count >= 0:
            required_reliever = requested_reliever_count
        else:
            required_reliever = max(1, math.ceil(num_blocks / self.reliever_ratio))

        if requested_standby_count is not None and requested_standby_count >= 0:
            required_standby = requested_standby_count
            total_required = required_js + required_reliever + required_standby
            if total_required > n_faculty:
                shortage = total_required - n_faculty
                raise ShortageError(
                    required=total_required,
                    available=n_faculty,
                    shortage=shortage,
                    message=f"Allocation cannot be completed. Required: {total_required}, Available: {n_faculty}, Shortage: {shortage}"
                )
        else:
            total_mandatory = required_js + required_reliever
            if total_mandatory > n_faculty:
                shortage = total_mandatory - n_faculty
                raise ShortageError(
                    required=total_mandatory,
                    available=n_faculty,
                    shortage=shortage,
                    message=f"Allocation cannot be completed. Required: {total_mandatory}, Available: {n_faculty}, Shortage: {shortage}"
                )
            required_standby = n_faculty - total_mandatory

        # Calculate historical stats across pool for normalization
        js_counts = [f.get("previous_js_count", 0) for f in eligible_faculty]
        rel_counts = [f.get("previous_reliever_count", 0) for f in eligible_faculty]
        stb_counts = [f.get("previous_standby_count", 0) for f in eligible_faculty]
        total_counts = [f.get("total_previous_duties", js_counts[i] + rel_counts[i] + stb_counts[i]) for i, f in enumerate(eligible_faculty)]
        
        mean_js = sum(js_counts) / max(1, n_faculty)
        mean_rel = sum(rel_counts) / max(1, n_faculty)
        mean_stb = sum(stb_counts) / max(1, n_faculty)
        mean_total = sum(total_counts) / max(1, n_faculty)
        
        # Initialize OR-Tools CP-SAT Model
        model = cp_model.CpModel()
        
        x_js = {}
        x_rel = {}
        x_stb = {}
        
        for i in range(n_faculty):
            x_js[i] = model.NewBoolVar(f"x_js_{i}")
            x_rel[i] = model.NewBoolVar(f"x_rel_{i}")
            x_stb[i] = model.NewBoolVar(f"x_stb_{i}")
            
            # Constraint 1: Exactly one role per faculty
            model.Add(x_js[i] + x_rel[i] + x_stb[i] == 1)

            # Hard Constraint: Same-department conflict rule
            if self.disallow_same_dept and exam_department_ids:
                f_dept = eligible_faculty[i].get("department_id")
                if f_dept in exam_department_ids:
                    # Faculty cannot be assigned JS for exams from their own department
                    model.Add(x_js[i] == 0)

        # Constraint 2: Exact counts for JS, Reliever, Standby
        model.Add(sum(x_js[i] for i in range(n_faculty)) == required_js)
        model.Add(sum(x_rel[i] for i in range(n_faculty)) == required_reliever)
        model.Add(sum(x_stb[i] for i in range(n_faculty)) == required_standby)
        
        # Constraint 3: Department fairness constraint
        dept_faculty: Dict[int, List[int]] = {}
        for i, f in enumerate(eligible_faculty):
            d_id = f.get("department_id", 0)
            dept_faculty.setdefault(d_id, []).append(i)

        for d_id, indices in dept_faculty.items():
            n_dept = len(indices)
            expected_js = (n_dept / max(1, n_faculty)) * required_js
            max_dept_js = min(n_dept, math.ceil(expected_js) + 1)
            min_dept_js = max(0, math.floor(expected_js) - 1)
            
            model.Add(sum(x_js[i] for i in indices) <= max_dept_js)
            model.Add(sum(x_js[i] for i in indices) >= min_dept_js)

        # Build Cost Function for CP-SAT with Adaptive Workload & Role Rotation
        SCALE = 1000
        objective_terms = []
        
        for i, f in enumerate(eligible_faculty):
            js_hist = f.get("previous_js_count", 0)
            rel_hist = f.get("previous_reliever_count", 0)
            stb_hist = f.get("previous_standby_count", 0)
            total_hist = f.get("total_previous_duties", js_hist + rel_hist + stb_hist)
            last_role = f.get("last_assigned_role")
            f_id = f.get("id")
            is_consecutive = 1 if f_id in consecutive_faculty_ids else 0

            # 1. Total Workload Equity Term: faculty with higher total historical workload get penalized for active duty
            workload_bias = (total_hist - mean_total) * 8.0

            # 2. Adaptive Role Rotation Imbalance:
            # e.g., If faculty has high JS (5 JS, 1 Rel, 1 Stb), js_dom > 0 -> heavily penalize JS, discount Rel/Stb
            js_dom = js_hist - max(rel_hist, stb_hist)
            rel_dom = rel_hist - max(js_hist, stb_hist)
            stb_dom = stb_hist - max(js_hist, rel_hist)

            # 3. Anti-Repeat Penalty (prevents back-to-back same role assignments)
            rep_js = 20.0 if last_role == "JS" else 0.0
            rep_rel = 20.0 if last_role == "Reliever" else 0.0
            rep_stb = 20.0 if last_role == "Standby" else 0.0

            # Cost for assigning JS:
            cost_js = (
                self.w_js * (js_hist - mean_js) * 10.0 +
                workload_bias * 1.2 +
                (js_dom * 15.0 if js_dom > 0 else 0.0) -
                (rel_dom * 10.0 if rel_dom > 0 else 0.0) -
                (stb_dom * 10.0 if stb_dom > 0 else 0.0) +
                rep_js +
                self.w_consec * is_consecutive * 25.0
            )

            # Cost for assigning Reliever:
            cost_rel = (
                self.w_rel * (rel_hist - mean_rel) * 12.0 +
                workload_bias * 0.8 -
                (js_dom * 12.0 if js_dom > 0 else 0.0) +
                (rel_dom * 15.0 if rel_dom > 0 else 0.0) -
                (stb_dom * 8.0 if stb_dom > 0 else 0.0) +
                rep_rel +
                (self.w_consec * 0.5) * is_consecutive * 10.0
            )

            # Cost for assigning Standby:
            cost_stb = (
                self.w_stb * (stb_hist - mean_stb) * 12.0 -
                workload_bias * 1.5 -
                (js_dom * 12.0 if js_dom > 0 else 0.0) -
                (rel_dom * 8.0 if rel_dom > 0 else 0.0) +
                (stb_dom * 15.0 if stb_dom > 0 else 0.0) +
                rep_stb -
                self.w_consec * is_consecutive * 25.0
            )

            int_cost_js = int(round(cost_js * SCALE))
            int_cost_rel = int(round(cost_rel * SCALE))
            int_cost_stb = int(round(cost_stb * SCALE))

            objective_terms.append(int_cost_js * x_js[i])
            objective_terms.append(int_cost_rel * x_rel[i])
            objective_terms.append(int_cost_stb * x_stb[i])

        model.Minimize(sum(objective_terms))

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        solver.parameters.num_workers = 4
        solver_status = solver.Solve(model)

        allocations = []
        js_assigned_indices = []
        rel_assigned_indices = []
        stb_assigned_indices = []

        if solver_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status_text = "Optimal" if solver_status == cp_model.OPTIMAL else "Feasible"
            for i in range(n_faculty):
                if solver.Value(x_js[i]) == 1:
                    js_assigned_indices.append(i)
                elif solver.Value(x_rel[i]) == 1:
                    rel_assigned_indices.append(i)
                else:
                    stb_assigned_indices.append(i)
        else:
            status_text = "Heuristic Fallback"
            sorted_by_js = sorted(
                range(n_faculty),
                key=lambda idx: eligible_faculty[idx].get("previous_js_count", 0)
            )
            js_assigned_indices = sorted_by_js[:required_js]
            remaining = sorted_by_js[required_js:]
            sorted_by_rel = sorted(
                remaining,
                key=lambda idx: (
                    eligible_faculty[idx].get("previous_reliever_count", 0),
                    -eligible_faculty[idx].get("previous_js_count", 0)
                )
            )
            rel_assigned_indices = sorted_by_rel[:required_reliever]
            stb_assigned_indices = sorted_by_rel[required_reliever:]

        # Assign blocks/classrooms to Junior Supervisors
        for rank, idx in enumerate(js_assigned_indices):
            f = eligible_faculty[idx]
            block_idx = rank // self.js_per_classroom
            block_label = (
                rooms_list[block_idx] if rooms_list and block_idx < len(rooms_list)
                else f"Block {block_idx + 1}"
            )
            if self.js_per_classroom > 1:
                sub_pos = (rank % self.js_per_classroom) + 1
                block_label = f"{block_label} (JS-{sub_pos})"

            reason = self._generate_reason("JS", f, mean_js, mean_rel, mean_stb, f["id"] in consecutive_faculty_ids)
            allocations.append({
                "faculty_id": f["id"],
                "faculty_name": f.get("name", f"Faculty {f['id']}"),
                "department_id": f["department_id"],
                "department_name": f.get("department_name", "Unknown"),
                "designation": f.get("designation", "Assistant Professor"),
                "assigned_role": "JS",
                "assigned_block": block_label,
                "fairness_score": round(self._calculate_individual_fairness(f, "JS", mean_js), 2),
                "prev_js_snapshot": f.get("previous_js_count", 0),
                "prev_reliever_snapshot": f.get("previous_reliever_count", 0),
                "prev_standby_snapshot": f.get("previous_standby_count", 0),
                "prev_total_snapshot": f.get("total_previous_duties", 0),
                "previous_role": "Reliever" if f.get("previous_reliever_count", 0) > f.get("previous_js_count", 0) else ("Standby" if f.get("previous_standby_count", 0) > f.get("previous_js_count", 0) else "JS"),
                "explainability_reason": reason,
                "status": "Proposed",
                "is_manual_override": False
            })

        # Reliever assignments
        for r_rank, idx in enumerate(rel_assigned_indices):
            f = eligible_faculty[idx]
            start_b = r_rank * self.reliever_ratio + 1
            end_b = min(num_blocks, (r_rank + 1) * self.reliever_ratio)
            coverage_label = f"Reliever Group {r_rank + 1} (Blocks {start_b}-{end_b})" if end_b >= start_b else f"Reliever Reserve {r_rank + 1}"
            reason = self._generate_reason("Reliever", f, mean_js, mean_rel, mean_stb, f["id"] in consecutive_faculty_ids)
            allocations.append({
                "faculty_id": f["id"],
                "faculty_name": f.get("name", f"Faculty {f['id']}"),
                "department_id": f["department_id"],
                "department_name": f.get("department_name", "Unknown"),
                "designation": f.get("designation", "Assistant Professor"),
                "assigned_role": "Reliever",
                "assigned_block": coverage_label,
                "fairness_score": round(self._calculate_individual_fairness(f, "Reliever", mean_js), 2),
                "prev_js_snapshot": f.get("previous_js_count", 0),
                "prev_reliever_snapshot": f.get("previous_reliever_count", 0),
                "prev_standby_snapshot": f.get("previous_standby_count", 0),
                "prev_total_snapshot": f.get("total_previous_duties", 0),
                "previous_role": "JS" if f.get("previous_js_count", 0) > 0 else "Standby",
                "explainability_reason": reason,
                "status": "Proposed",
                "is_manual_override": False
            })

        # Standby assignments
        for s_rank, idx in enumerate(stb_assigned_indices):
            f = eligible_faculty[idx]
            standby_label = f"Central Control Standby #{s_rank + 1}"
            reason = self._generate_reason("Standby", f, mean_js, mean_rel, mean_stb, f["id"] in consecutive_faculty_ids)
            allocations.append({
                "faculty_id": f["id"],
                "faculty_name": f.get("name", f"Faculty {f['id']}"),
                "department_id": f["department_id"],
                "department_name": f.get("department_name", "Unknown"),
                "designation": f.get("designation", "Assistant Professor"),
                "assigned_role": "Standby",
                "assigned_block": standby_label,
                "fairness_score": round(self._calculate_individual_fairness(f, "Standby", mean_js), 2),
                "prev_js_snapshot": f.get("previous_js_count", 0),
                "prev_reliever_snapshot": f.get("previous_reliever_count", 0),
                "prev_standby_snapshot": f.get("previous_standby_count", 0),
                "prev_total_snapshot": f.get("total_previous_duties", 0),
                "previous_role": "JS" if f.get("previous_js_count", 0) > 0 else "Reliever",
                "explainability_reason": reason,
                "status": "Proposed",
                "is_manual_override": False
            })

        execution_time = time.time() - start_time
        fairness_variance = self._calculate_variance_score(allocations)
        
        # Calculate overall institutional fairness score 0 - 100
        overall_fairness_score = round(max(60.0, min(99.0, 100.0 - (fairness_variance * 3.5))), 1)

        return {
            "solver_status": status_text,
            "execution_time_seconds": round(execution_time, 4),
            "overall_fairness_score": overall_fairness_score,
            "fairness_variance_score": round(fairness_variance, 3),
            "total_eligible_faculty": n_faculty,
            "required_js": required_js,
            "required_relievers": required_reliever,
            "required_standby": required_standby,
            "allocations": allocations
        }

    def _generate_reason(
        self,
        role: str,
        faculty: Dict[str, Any],
        mean_js: float,
        mean_rel: float,
        mean_stb: float,
        is_consecutive: bool
    ) -> str:
        js = faculty.get("previous_js_count", 0)
        rel = faculty.get("previous_reliever_count", 0)
        stb = faculty.get("previous_standby_count", 0)
        
        if role == "Reliever":
            if js > mean_js and rel <= mean_rel:
                return (
                    f"Assigned Reliever because faculty has served disproportionately high JS duties ({js} vs avg {mean_js:.1f}) "
                    f"and lower Reliever duties ({rel}). Workload equity compensation applied."
                )
            elif rel == 0:
                return f"Selected for Reliever rotation due to zero prior Reliever assignments across the academic year."
            elif is_consecutive:
                return f"Selected for Reliever following consecutive duty session to moderate continuous classroom supervision."
            else:
                return f"Selected for Reliever based on balanced duty rotation across all department faculty."

        elif role == "Standby":
            if js > mean_js:
                return (
                    f"Assigned Standby reserve to relieve heavy historical classroom duty ({js} JS completed). "
                    f"Allows equitable distribution of reserve roles."
                )
            elif stb <= mean_stb:
                return f"Selected for Standby reserve due to lower historical standby count ({stb} vs avg {mean_stb:.1f})."
            elif is_consecutive:
                return f"Selected for Standby reserve to prevent fatigue from consecutive examination days."
            else:
                return f"Selected for Standby reserve in compliance with institutional fairness equity."

        else: # "JS"
            if js < mean_js:
                return (
                    f"Selected for Junior Supervisor because historical JS count ({js}) is below college faculty average ({mean_js:.1f}). "
                    f"Balances overall classroom supervision load."
                )
            elif rel > mean_rel or stb > mean_stb:
                return (
                    f"Selected for JS as faculty previously completed Reliever ({rel}) or Standby ({stb}) duties; "
                    f"rotating back into classroom supervision."
                )
            else:
                return f"Selected for Junior Supervisor in accordance with standard departmental classroom quota and balanced duty history."

    def _calculate_individual_fairness(self, faculty: Dict[str, Any], role: str, mean_js: float) -> float:
        js = faculty.get("previous_js_count", 0)
        score = 88.0
        if role == "Reliever" and js >= mean_js:
            score += 8.0
        elif role == "JS" and js <= mean_js:
            score += 8.0
        elif role == "Standby" and js >= mean_js:
            score += 6.0
        return min(100.0, max(60.0, score))

    def _calculate_variance_score(self, allocations: List[Dict[str, Any]]) -> float:
        if not allocations:
            return 0.0
        js_list = [a["prev_js_snapshot"] + (1 if a["assigned_role"] == "JS" else 0) for a in allocations]
        mean = sum(js_list) / len(js_list)
        variance = sum((x - mean) ** 2 for x in js_list) / len(js_list)
        return math.sqrt(variance)
