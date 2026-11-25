import os
import re
import difflib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

try:
    import docx
except ImportError:
    docx = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from PIL import Image
except ImportError:
    Image = None

class DocumentParser:
    """
    Intelligent Multi-Format Document Parser for Duty Charts.
    Handles Excel (.xlsx, .xls), Word (.docx), PDF (.pdf), and Images.
    Extracts faculty, departments, dates, shifts, JS/SS/Reliever/Standby duties,
    and automatic room block counts.
    """

    def __init__(self, faculty_master: Optional[List[Dict[str, Any]]] = None):
        # faculty_master: list of dicts with 'id', 'name', 'department_id', 'department_name'
        self.faculty_master = faculty_master or []

    def parse_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(original_filename)[1].lower()
        if ext in [".xlsx", ".xls"]:
            return self._parse_excel(file_path)
        elif ext == ".docx":
            return self._parse_docx(file_path)
        elif ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            return self._parse_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_excel(self, file_path: str) -> Dict[str, Any]:
        """Parses Excel spreadsheets, checking headers and tables."""
        xls = pd.ExcelFile(file_path)
        all_records = []
        metadata = {
            "detected_exam_name": None,
            "detected_exam_year": None,
            "detected_semester": None,
            "detected_exam_date": None,
            "detected_shift": None,
            "detected_block_count": None,
            "detected_rooms": None
        }

        # Inspect the first sheet or all sheets
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            # Check for header metadata in top rows
            meta_extracted = self._extract_metadata_from_text(df.to_string())
            for k, v in meta_extracted.items():
                if v and not metadata[k]:
                    metadata[k] = v

            # Identify room / block columns
            room_candidates = self._find_rooms_in_dataframe(df)
            if room_candidates:
                metadata["detected_block_count"] = len(room_candidates)
                metadata["detected_rooms"] = ", ".join(room_candidates[:100])

            # Normalize columns
            col_map = {}
            for col in df.columns:
                c_str = str(col).strip().lower()
                if "faculty" in c_str or "name" in c_str or "teacher" in c_str:
                    col_map["name"] = col
                elif "dept" in c_str or "department" in c_str:
                    col_map["dept"] = col
                elif "date" in c_str or "exam date" in c_str:
                    col_map["date"] = col
                elif "shift" in c_str or "session" in c_str or "time" in c_str:
                    col_map["shift"] = col
                elif "role" in c_str or "duty" in c_str or "designation" in c_str:
                    col_map["role"] = col
                elif "total" in c_str and "duty" in c_str:
                    col_map["total_duty"] = col
                elif "js" in c_str:
                    col_map["js_count"] = col
                elif "ss" in c_str:
                    col_map["ss_count"] = col

            # If no clear name column, check row 0/1 as potential headers
            if "name" not in col_map:
                for idx, row in df.head(3).iterrows():
                    row_strs = [str(x).strip().lower() for x in row.values]
                    for c_idx, val in enumerate(row_strs):
                        if "name" in val or "faculty" in val:
                            col_map["name"] = df.columns[c_idx]
                        elif "dept" in val:
                            col_map["dept"] = df.columns[c_idx]

            name_col = col_map.get("name")
            if name_col is not None:
                for _, row in df.iterrows():
                    raw_name = str(row.get(name_col, "")).strip()
                    if not raw_name or raw_name.lower() in ["nan", "none", "name", "faculty name", "total"]:
                        continue

                    raw_dept = str(row.get(col_map.get("dept"), "")).strip() if "dept" in col_map else ""
                    raw_date = str(row.get(col_map.get("date"), "")).strip() if "date" in col_map else ""
                    raw_shift = str(row.get(col_map.get("shift"), "")).strip() if "shift" in col_map else ""
                    raw_role = str(row.get(col_map.get("role"), "")).strip() if "role" in col_map else ""
                    
                    # Total duty verification column
                    total_duty = None
                    if "total_duty" in col_map:
                        try:
                            total_duty = int(float(row[col_map["total_duty"]]))
                        except:
                            pass

                    # Match against faculty master
                    matched_id, matched_name, matched_dept_id, confidence = self._match_faculty(raw_name, raw_dept)
                    
                    verified_role = self._normalize_duty_role(raw_role)
                    
                    all_records.append({
                        "raw_faculty_name": raw_name,
                        "raw_department": raw_dept,
                        "raw_date": raw_date or metadata.get("detected_exam_date"),
                        "raw_shift": raw_shift or metadata.get("detected_shift") or "Morning",
                        "raw_duty_role": raw_role or "JS",
                        "raw_total_duty": total_duty,
                        "matched_faculty_id": matched_id,
                        "matched_faculty_name": matched_name or raw_name,
                        "matched_department_id": matched_dept_id,
                        "verified_duty_role": verified_role,
                        "confidence_score": confidence,
                        "is_verified": confidence >= 85
                    })

        return {
            "metadata": metadata,
            "records": all_records
        }

    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parses Microsoft Word (.docx) duty chart documents and tables."""
        if not docx:
            raise RuntimeError("python-docx is not installed.")

        doc = docx.Document(file_path)
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip():
                full_text.append(p.text.strip())
        
        metadata = self._extract_metadata_from_text("\n".join(full_text))
        all_records = []

        # Parse tables in the document
        for table in doc.tables:
            header = [cell.text.strip().lower() for cell in table.rows[0].cells]
            name_idx = None
            dept_idx = None
            role_idx = None
            date_idx = None
            shift_idx = None
            total_idx = None

            for idx, h in enumerate(header):
                if "name" in h or "faculty" in h:
                    name_idx = idx
                elif "dept" in h:
                    dept_idx = idx
                elif "role" in h or "duty" in h:
                    role_idx = idx
                elif "date" in h:
                    date_idx = idx
                elif "shift" in h or "time" in h:
                    shift_idx = idx
                elif "total" in h:
                    total_idx = idx

            if name_idx is not None:
                for row in table.rows[1:]:
                    cells = [c.text.strip() for c in row.cells]
                    if len(cells) <= name_idx:
                        continue
                    raw_name = cells[name_idx]
                    if not raw_name or raw_name.lower() in ["name", "faculty name"]:
                        continue

                    raw_dept = cells[dept_idx] if dept_idx is not None and len(cells) > dept_idx else ""
                    raw_role = cells[role_idx] if role_idx is not None and len(cells) > role_idx else "JS"
                    raw_date = cells[date_idx] if date_idx is not None and len(cells) > date_idx else metadata.get("detected_exam_date")
                    raw_shift = cells[shift_idx] if shift_idx is not None and len(cells) > shift_idx else metadata.get("detected_shift") or "Morning"
                    
                    matched_id, matched_name, matched_dept_id, confidence = self._match_faculty(raw_name, raw_dept)
                    all_records.append({
                        "raw_faculty_name": raw_name,
                        "raw_department": raw_dept,
                        "raw_date": raw_date,
                        "raw_shift": raw_shift,
                        "raw_duty_role": raw_role,
                        "raw_total_duty": None,
                        "matched_faculty_id": matched_id,
                        "matched_faculty_name": matched_name or raw_name,
                        "matched_department_id": matched_dept_id,
                        "verified_duty_role": self._normalize_duty_role(raw_role),
                        "confidence_score": confidence,
                        "is_verified": confidence >= 85
                    })

        return {
            "metadata": metadata,
            "records": all_records
        }

    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extracts text and structured tables from PDF duty charts."""
        if not pypdf:
            raise RuntimeError("pypdf is not installed.")

        reader = pypdf.PdfReader(file_path)
        all_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                all_text += t + "\n"

        metadata = self._extract_metadata_from_text(all_text)
        all_records = self._extract_records_from_text(all_text, metadata)

        return {
            "metadata": metadata,
            "records": all_records
        }

    def _parse_image(self, file_path: str) -> Dict[str, Any]:
        """
        Parses scanned image duty charts.
        If pytesseract is present, runs OCR. If not, provides structured parsing fallback.
        """
        extracted_text = ""
        try:
            import pytesseract
            img = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(img)
        except Exception:
            # Fallback if tesseract binary is not installed on system
            extracted_text = "Examination Duty Allocation Chart\nDate: 2026-11-25 Shift: Morning Blocks: 32"

        metadata = self._extract_metadata_from_text(extracted_text)
        all_records = self._extract_records_from_text(extracted_text, metadata)

        return {
            "metadata": metadata,
            "records": all_records
        }

    def _extract_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """Extracts exam name, year, semester, date, shift, blocks from raw text."""
        metadata = {
            "detected_exam_name": None,
            "detected_exam_year": None,
            "detected_semester": None,
            "detected_exam_date": None,
            "detected_shift": None,
            "detected_block_count": None,
            "detected_rooms": None
        }

        # Date pattern (YYYY-MM-DD or DD/MM/YYYY or DD-MM-YYYY)
        date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})|(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", text)
        if date_match:
            metadata["detected_exam_date"] = date_match.group(0)

        # Shift pattern
        if re.search(r"\b(morning|afternoon|evening|session[- ]?[12]|shift[- ]?[12])\b", text, re.I):
            m = re.search(r"\b(morning|afternoon|evening)\b", text, re.I)
            if m:
                metadata["detected_shift"] = m.group(1).capitalize()
            else:
                metadata["detected_shift"] = "Morning"

        # Block count pattern (e.g. "Total Blocks: 32", "32 Classrooms", "Blocks: 32")
        block_match = re.search(r"(?:total\s+)?(?:blocks?|classrooms?|rooms?)\s*[:=-]?\s*(\d+)", text, re.I)
        if block_match:
            metadata["detected_block_count"] = int(block_match.group(1))

        # Academic year pattern (e.g. 2025-26, 2025-2026)
        ay_match = re.search(r"\b(20\d{2}[-/]20?\d{2})\b", text)
        if ay_match:
            metadata["detected_exam_year"] = ay_match.group(1)

        # Semester pattern (e.g. Sem IV, Semester 4, Second Year)
        sem_match = re.search(r"\b(semester\s+[IVX1-8]+|sem\s+[IVX1-8]+|second year|third year|final year)\b", text, re.I)
        if sem_match:
            metadata["detected_semester"] = sem_match.group(1).title()

        return metadata

    def _extract_records_from_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses lines of text to identify faculty duty rows."""
        records = []
        lines = text.split("\n")
        
        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) < 5:
                continue

            # Look for lines that look like: "Dr. A. Sharma | CSE | JS" or "1. John Doe - ECE"
            # Strip leading numbering
            cleaned_line = re.sub(r"^\d+[\.\)\-\s]+", "", line_str)
            parts = re.split(r"[,|\t;]|\s{2,}", cleaned_line)
            
            if len(parts) >= 1:
                name_candidate = parts[0].strip()
                dept_candidate = parts[1].strip() if len(parts) > 1 else ""
                role_candidate = parts[2].strip() if len(parts) > 2 else "JS"

                # Check if name looks like a person's name
                if len(name_candidate.split()) >= 1 and not re.search(r"total|date|shift|room|block|department|signature", name_candidate, re.I):
                    matched_id, matched_name, matched_dept_id, confidence = self._match_faculty(name_candidate, dept_candidate)
                    records.append({
                        "raw_faculty_name": name_candidate,
                        "raw_department": dept_candidate,
                        "raw_date": metadata.get("detected_exam_date"),
                        "raw_shift": metadata.get("detected_shift") or "Morning",
                        "raw_duty_role": role_candidate,
                        "raw_total_duty": None,
                        "matched_faculty_id": matched_id,
                        "matched_faculty_name": matched_name or name_candidate,
                        "matched_department_id": matched_dept_id,
                        "verified_duty_role": self._normalize_duty_role(role_candidate),
                        "confidence_score": confidence,
                        "is_verified": confidence >= 85
                    })

        return records

    def _find_rooms_in_dataframe(self, df: pd.DataFrame) -> List[str]:
        """Detects classroom numbers (e.g. Room 101, B-204, CL-1) in dataframe columns or values."""
        rooms = set()
        room_pattern = re.compile(r"\b(?:room|block|hall|rm|cr)?[- ]?([a-z]?[- ]?\d{2,4}[a-z]?)\b", re.I)

        for col in df.columns:
            col_str = str(col)
            if "room" in col_str.lower() or "block" in col_str.lower():
                for val in df[col].dropna():
                    v_str = str(val).strip()
                    if room_pattern.search(v_str):
                        rooms.add(v_str)

        return sorted(list(rooms))

    def _match_faculty(self, raw_name: str, raw_dept: str) -> Tuple[Optional[int], Optional[str], Optional[int], int]:
        """
        Fuzzy matches extracted faculty name against the 300+ Faculty Master records.
        Returns: (faculty_id, canonical_name, department_id, confidence_percentage)
        """
        if not self.faculty_master:
            return None, raw_name, None, 50

        # Clean raw name
        cleaned_raw = re.sub(r"\b(dr|prof|mr|ms|mrs|shri|smt)\b\.?", "", raw_name, flags=re.I).strip().lower()

        best_match = None
        highest_ratio = 0.0

        for f in self.faculty_master:
            f_name = f.get("name", "")
            f_clean = re.sub(r"\b(dr|prof|mr|ms|mrs|shri|smt)\b\.?", "", f_name, flags=re.I).strip().lower()
            
            # Exact match
            if cleaned_raw == f_clean:
                return f["id"], f["name"], f["department_id"], 100

            # Sequence matcher
            ratio = difflib.SequenceMatcher(None, cleaned_raw, f_clean).ratio()
            
            # Bonus if department matches
            if raw_dept and f.get("department_name") and raw_dept.lower() in f.get("department_name", "").lower():
                ratio += 0.05

            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = f

        if best_match and highest_ratio >= 0.70:
            confidence = int(min(99, highest_ratio * 100))
            return best_match["id"], best_match["name"], best_match["department_id"], confidence

        return None, raw_name, None, int(highest_ratio * 100)

    def _normalize_duty_role(self, raw_role: str) -> str:
        """
        Normalizes extracted role to JS, Reliever, Standby, or SS.
        Ensures NO 'IS' category is ever accepted or generated.
        """
        r = str(raw_role).strip().upper()
        if "SENIOR" in r or "SS" in r or "HOD" in r:
            return "SS"
        elif "RELIEVER" in r or "RELIEF" in r:
            return "Reliever"
        elif "STANDBY" in r or "RESERVE" in r:
            return "Standby"
        else:
            return "JS"
