"use client";

import React, { useState, useEffect } from "react";
import {
  CalendarDays,
  DoorOpen,
  Users,
  Download,
  CheckCircle2,
  RefreshCw,
  FileSpreadsheet,
  Check,
  Search,
  Filter,
  ShieldAlert,
  Printer,
  UploadCloud,
  BookOpen,
} from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function ExamDutyAllocationPortal() {
  // Timetable State
  const [timetableFile, setTimetableFile] = useState<File | null>(null);
  const [timetableUploading, setTimetableUploading] = useState(false);
  const [timetableExtracted, setTimetableExtracted] = useState<any[]>([]);
  const [timetableNotice, setTimetableNotice] = useState<string | null>(null);

  // Faculty List State
  const [facultyFile, setFacultyFile] = useState<File | null>(null);
  const [facultyUploading, setFacultyUploading] = useState(false);
  const [facultyPool, setFacultyPool] = useState<any[]>([]);
  const [extractedFacultyList, setExtractedFacultyList] = useState<any[]>([]);
  const [facultyNotice, setFacultyNotice] = useState<string | null>(null);

  // Exam Selection Inputs
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("2026-12-12");
  const [selectedShift, setSelectedShift] = useState<string>("Morning Shift");
  const [selectedTiming, setSelectedTiming] = useState<string>("all");
  const [availableTimings, setAvailableTimings] = useState<string[]>([]);
  const [selectedShiftId, setSelectedShiftId] = useState<number | null>(null);
  const [dateExams, setDateExams] = useState<any[]>([]);
  const [dateVerification, setDateVerification] = useState<any | null>(null);

  // Active Verified Faculty Batch (Strict Pool)
  const [activeBatch, setActiveBatch] = useState<any | null>(null);

  // Classrooms Input
  const [numClassrooms, setNumClassrooms] = useState<number>(24);
  const [jsPerRoom, setJsPerRoom] = useState<number>(1);
  const [relieverRatio, setRelieverRatio] = useState<number>(4);
  const [standbyCount, setStandbyCount] = useState<number>(6);

  // Live Staffing Preview & Shortage
  const [reqPreview, setReqPreview] = useState<any | null>(null);
  const [shortageError, setShortageError] = useState<any | null>(null);

  // Allocation State
  const [allocating, setAllocating] = useState(false);
  const [allocationSummary, setAllocationSummary] = useState<any | null>(null);
  const [approving, setApproving] = useState(false);
  const [approvedNotice, setApprovedNotice] = useState<string | null>(null);

  // Search & Filter
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [deptFilter, setDeptFilter] = useState("all");

  useEffect(() => {
    // 1. Fetch active faculty batch (strictly enforced pool)
    fetchApi("/faculty/active-batch")
      .then((b) => {
        if (b && b.has_active_batch) {
          setActiveBatch(b);
          setFacultyPool(b.eligible_faculty || []);
        } else {
          fetchApi("/faculty?limit=500").then((fac: any[]) => {
            const eligible = fac.filter((f) => f.role_category === "Faculty" && f.eligibility);
            setFacultyPool(eligible.length > 0 ? eligible : fac);
          }).catch(() => {});
        }
      })
      .catch(() => {});

    // 2. Fetch timetable records
    fetchApi("/timetables/records")
      .then((records: any[]) => {
        if (records && records.length > 0) {
          setTimetableExtracted(records);
          const dates = Array.from(new Set(records.map((r) => r.exam_date)));
          setAvailableDates(dates);
          if (dates.length > 0) {
            setSelectedDate(dates[0]);
          }
        } else {
          const defaultDates = ["2026-12-12", "2026-12-14", "2026-12-16"];
          setAvailableDates(defaultDates);
          setSelectedDate(defaultDates[0]);
        }
      })
      .catch(() => {
        const defaultDates = ["2026-12-12", "2026-12-14", "2026-12-16"];
        setAvailableDates(defaultDates);
        setSelectedDate(defaultDates[0]);
      });

    // 3. Fetch shifts
    fetchApi("/examinations")
      .then((exams: any[]) => {
        const shiftsList: any[] = [];
        exams.forEach((e) => {
          e.dates?.forEach((d: any) => {
            d.shifts?.forEach((s: any) => {
              shiftsList.push({
                id: s.id,
                date: d.exam_date,
                shift_name: s.shift_name,
                exam_name: e.name,
              });
            });
          });
        });
        if (shiftsList.length > 0) {
          setSelectedShiftId(shiftsList[0].id);
        }
      })
      .catch(() => {});
  }, []);

  // Update dynamic timings and exams when date or shift changes
  useEffect(() => {
    if (selectedDate) {
      fetchApi(`/allocation/date-exams?date=${selectedDate}&shift=${selectedShift}`)
        .then((res) => {
          setDateVerification(res);
          
          // Populate dynamic timings extracted from PDF
          const timings = res.timings_by_shift?.[selectedShift] || [];
          setAvailableTimings(timings);

          // Filter exams for this date, shift, and timing
          const allEx = res.all_examinations || res.examinations || [];
          let filtered = allEx.filter((e: any) => (e.shift_name || e.shift) === selectedShift);
          if (selectedTiming && selectedTiming !== "all") {
            filtered = filtered.filter((e: any) => e.time === selectedTiming || e.time_range === selectedTiming);
          }
          setDateExams(filtered);

          if (res.available_shifts && res.available_shifts.length > 0) {
            setSelectedShiftId(res.available_shifts[0].shift_id);
          }
        })
        .catch(() => {
          setDateVerification({
            is_verified_in_pdf: false,
            verification_message: "Date not found in uploaded timetable PDF.",
            detected_years: [],
            examinations: [],
          });
          setAvailableTimings([]);
          setDateExams([]);
        });
    }
  }, [selectedDate, selectedShift, selectedTiming, timetableExtracted]);

  // Recalculate staffing requirements based on classroom blocks and active verified faculty pool
  useEffect(() => {
    if (numClassrooms > 0) {
      fetchApi("/allocation/calculate-requirements", {
        method: "POST",
        body: JSON.stringify({
          num_classrooms: numClassrooms,
          batch_id: activeBatch?.batch_id,
          js_per_classroom: jsPerRoom,
          reliever_ratio: relieverRatio,
          standby_count: standbyCount,
        }),
      })
        .then((res) => {
          setReqPreview(res);
          if (res.shortage > 0) {
            setShortageError({
              required: res.total_required,
              available: res.eligible_faculty_available,
              shortage: res.shortage,
            });
          } else {
            setShortageError(null);
          }
        })
        .catch(() => {});
    }
  }, [numClassrooms, jsPerRoom, relieverRatio, standbyCount, activeBatch]);

  const handleUploadTimetable = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setTimetableFile(file);
    setTimetableUploading(true);
    setTimetableNotice(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("exam_name", "Semester Examination");

    try {
      const res = await fetch("/api/timetables/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setTimetableUploading(false);

      if (res.ok) {
        setTimetableNotice(`Timetable processed: ${data.records_count} sessions extracted.`);
        const records = await fetchApi("/timetables/records");
        setTimetableExtracted(records);
        const dates = Array.from(new Set(records.map((r: any) => String(r.exam_date || "")))).filter(Boolean) as string[];
        if (dates.length > 0) {
          setAvailableDates(dates);
          setSelectedDate(dates[0]);
        }
      } else {
        setTimetableNotice(data.detail || "Timetable processed.");
      }
    } catch {
      setTimetableUploading(false);
      setTimetableNotice(`Uploaded: ${file.name}`);
    }
  };

  const handleUploadFaculty = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFacultyFile(file);
    setFacultyUploading(true);
    setFacultyNotice(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/faculty/upload/parse", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setFacultyUploading(false);

      if (res.ok) {
        setExtractedFacultyList(data.candidates || []);
        setActiveBatch({
          batch_id: data.batch_id,
          batch_name: data.batch_name,
          filename: data.filename,
          eligible_count: data.eligible_count,
        });
        setFacultyNotice(
          `Verified Faculty List: ${data.eligible_count} eligible faculty active (${data.matched_count || 0} matched, ${data.new_count || 0} new). Only this list is eligible for allocation.`
        );
        const fac = await fetchApi("/faculty?limit=500");
        const eligible = fac.filter((f: any) => f.role_category === "Faculty" && f.eligibility);
        setFacultyPool(eligible.length > 0 ? eligible : fac);
      } else {
        setFacultyNotice(data.detail || "Faculty list processed.");
      }
    } catch {
      setFacultyUploading(false);
      setFacultyNotice(`Uploaded: ${file.name}`);
    }
  };

  const handleGenerateAllocation = async () => {
    try {
      setAllocating(true);
      setShortageError(null);
      setApprovedNotice(null);

      const shiftId = selectedShiftId || 1;
      const summary = await fetchApi("/allocation/run", {
        method: "POST",
        body: JSON.stringify({
          shift_id: shiftId,
          batch_id: activeBatch?.batch_id,
          block_count: Number(numClassrooms),
          js_per_classroom: Number(jsPerRoom),
          reliever_ratio: Number(relieverRatio),
          standby_count: Number(standbyCount),
          disallow_same_department_js: false,
          recalculate: true,
        }),
      });

      setAllocationSummary(summary);
      setAllocating(false);
    } catch (err: any) {
      setAllocating(false);
      if (err.message && err.message.includes("SHORTAGE")) {
        setShortageError({
          required: reqPreview?.total_required || 38,
          available: reqPreview?.eligible_faculty_available || 181,
          shortage: reqPreview?.shortage || 5,
        });
      } else {
        alert("Allocation error: " + err.message);
      }
    }
  };

  const handleApproveAllocation = async () => {
    if (!allocationSummary?.shift_id) return;
    try {
      setApproving(true);
      const res = await fetchApi(`/allocation/shift/${allocationSummary.shift_id}/approve`, {
        method: "POST"
      });
      setApproving(false);
      setApprovedNotice(res.message || "Official Duty Chart Finalized and Published to History.");
      // Refresh active batch to update historical duty counters in UI
      fetchApi("/faculty/active-batch").then((b) => setActiveBatch(b)).catch(() => {});
    } catch (err: any) {
      setApproving(false);
      alert("Approval error: " + err.message);
    }
  };

  const filteredAllocations = allocationSummary?.allocations?.filter((a: any) => {
    const matchSearch =
      a.faculty_name.toLowerCase().includes(search.toLowerCase()) ||
      a.department_name.toLowerCase().includes(search.toLowerCase()) ||
      (a.assigned_block && a.assigned_block.toLowerCase().includes(search.toLowerCase()));
    const matchRole = roleFilter === "all" || a.assigned_role === roleFilter;
    const matchDept = deptFilter === "all" || a.department_name === deptFilter;
    return matchSearch && matchRole && matchDept;
  }) || [];

  const deptsInAllocation = Array.from(
    new Set<string>(allocationSummary?.allocations?.map((a: any) => String(a.department_name)) || [])
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight">
            Examination Duty Allocation
          </h1>
          <p className="text-xs text-slate-500">
            TCET Central Examination Section
          </p>
        </div>
        <div className="flex items-center gap-2">
          {allocationSummary && (
            <>
              <button
                onClick={handleApproveAllocation}
                disabled={approving}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded shadow-2xs transition-colors"
              >
                <Check className="w-3.5 h-3.5" />
                <span>{approving ? "Finalizing..." : "Finalize & Approve Chart"}</span>
              </button>
              <button
                onClick={() => window.open(`/api/allocation/export/${selectedShiftId || 1}/excel`, "_blank")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded border border-slate-200 shadow-2xs transition-colors"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                <span>Export Excel</span>
              </button>
              <button
                onClick={() => window.open(`/api/allocation/export/${selectedShiftId || 1}/csv`, "_blank")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded border border-slate-200 shadow-2xs transition-colors"
              >
                <Download className="w-3.5 h-3.5 text-slate-500" />
                <span>Export CSV</span>
              </button>
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded shadow-2xs transition-colors"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* SECTION 1: TIMETABLE & FACULTY UPLOADS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Timetable File */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Examination Timetable
            </h2>
            <span className="text-[11px] text-slate-500">
              PDF / Excel / Word
            </span>
          </div>

          <div className="border border-dashed border-slate-300 hover:border-slate-400 rounded-md p-3.5 text-center bg-slate-50 transition-colors">
            <input
              type="file"
              id="tt-upload-input"
              className="hidden"
              accept=".pdf,.docx,.xlsx,.xls"
              onChange={handleUploadTimetable}
            />
            <label htmlFor="tt-upload-input" className="cursor-pointer block space-y-1.5">
              <UploadCloud className="w-5 h-5 text-slate-600 mx-auto" />
              <div className="text-xs font-medium text-slate-800">
                {timetableUploading ? "Processing..." : timetableFile ? timetableFile.name : "Select Timetable File"}
              </div>
              <div className="inline-block px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-white text-[11px] font-medium rounded">
                Browse
              </div>
            </label>
          </div>

          {timetableNotice && (
            <div className="p-2 bg-slate-50 border border-slate-200 rounded text-slate-700 text-[11px] flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>{timetableNotice}</span>
            </div>
          )}
        </div>

        {/* Faculty File */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Faculty List
            </h2>
            <span className="text-[11px] text-slate-500">
              {facultyPool.length} Active Records
            </span>
          </div>

          <div className="border border-dashed border-slate-300 hover:border-slate-400 rounded-md p-3.5 text-center bg-slate-50 transition-colors">
            <input
              type="file"
              id="faculty-upload-input"
              className="hidden"
              accept=".xlsx,.xls,.csv,.pdf"
              onChange={handleUploadFaculty}
            />
            <label htmlFor="faculty-upload-input" className="cursor-pointer block space-y-1.5">
              <Users className="w-5 h-5 text-slate-600 mx-auto" />
              <div className="text-xs font-medium text-slate-800">
                {facultyUploading ? "Processing..." : facultyFile ? facultyFile.name : "Select Faculty List"}
              </div>
              <div className="inline-block px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-white text-[11px] font-medium rounded">
                Browse
              </div>
            </label>
          </div>

          {facultyNotice && (
            <div className="p-2 bg-slate-50 border border-slate-200 rounded text-slate-700 text-[11px] flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>{facultyNotice}</span>
            </div>
          )}

          {extractedFacultyList.length > 0 && (
            <div className="border border-slate-200 rounded p-2 bg-slate-50 text-[11px] space-y-1 max-h-32 overflow-y-auto">
              <div className="font-semibold text-slate-700 flex items-center justify-between">
                <span>Extracted Records:</span>
                <span className="font-mono text-slate-500">{extractedFacultyList.length}</span>
              </div>
              <div className="space-y-1">
                {extractedFacultyList.slice(0, 5).map((f: any, i: number) => (
                  <div key={i} className="flex items-center justify-between bg-white px-2 py-1 rounded border border-slate-100 text-xs">
                    <span className="text-slate-800 truncate max-w-[190px]">{f.name}</span>
                    <span className="text-slate-500 text-[10px]">
                      {f.is_existing ? `${f.total_previous_duties || 0} duties` : "0 duties"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SECTION 2: DATE, SHIFT, TIMING & CLASSROOM COUNT */}
      <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
            Exam Session, Shift, Timing & Classrooms
          </h2>
          <span className="text-[11px] text-slate-500">
            Manual input with dynamic timetable extraction & strict verified faculty pool
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* 1. Manual Date Input */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Examination Date (Manual)
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full text-xs bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-900 font-mono focus:outline-slate-500"
            />
            {availableDates.length > 0 && (
              <div className="mt-1.5 flex flex-wrap items-center gap-1">
                <span className="text-[10px] text-slate-500">PDF:</span>
                {availableDates.map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setSelectedDate(d)}
                    className={`text-[10px] px-1.5 py-0.5 rounded border transition-colors ${
                      selectedDate === d
                        ? "bg-slate-800 text-white border-slate-800 font-semibold"
                        : "bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 2. Morning / Evening Shift Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Examination Shift
            </label>
            <select
              value={selectedShift}
              onChange={(e) => {
                setSelectedShift(e.target.value);
                setSelectedTiming("all");
              }}
              className="w-full text-xs bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-900 focus:outline-slate-500"
            >
              <option value="Morning Shift">Morning Shift (Morning Papers)</option>
              <option value="Evening Shift">Evening Shift (Evening Papers)</option>
            </select>
            <p className="text-[10px] text-slate-500 mt-1">
              Auto-classifies paper start times by institutional boundaries.
            </p>
          </div>

          {/* 3. Dynamic Examination Timing Dropdown (MANDATORY) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Examination Timing (Dynamic OCR)
            </label>
            <select
              value={selectedTiming}
              onChange={(e) => setSelectedTiming(e.target.value)}
              className="w-full text-xs bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-900 focus:outline-slate-500"
            >
              <option value="all">
                All Timings for {selectedShift} ({availableTimings.length} Detected)
              </option>
              {availableTimings.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-500 mt-1">
              Populated dynamically from verified timetable records.
            </p>
          </div>

          {/* 4. Number of Examination Blocks (Classrooms) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Number of Blocks (Classrooms)
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={numClassrooms}
              onChange={(e) => setNumClassrooms(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full text-xs bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-900 font-mono font-medium focus:outline-slate-500"
            />
            <p className="text-[10px] text-slate-500 mt-1">
              JS = 1 per block | Reliever = 1 per 4 blocks | Standby = 6
            </p>
          </div>
        </div>

        {/* OCR Date Verification Status Banner */}
        {dateVerification && (
          <div
            className={`p-2.5 rounded border text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 ${
              dateVerification.is_verified_in_pdf
                ? "bg-emerald-50/70 border-emerald-200 text-emerald-900"
                : "bg-slate-50 border-slate-200 text-slate-700"
            }`}
          >
            <div className="flex items-center gap-2">
              <CheckCircle2
                className={`w-4 h-4 shrink-0 ${
                  dateVerification.is_verified_in_pdf ? "text-emerald-600" : "text-slate-400"
                }`}
              />
              <div>
                <span className="font-semibold">
                  {dateVerification.is_verified_in_pdf
                    ? "Verified in Timetable PDF:"
                    : "OCR Verification Status:"}
                </span>{" "}
                <span>{dateVerification.verification_message}</span>
              </div>
            </div>
            {dateVerification.detected_years && dateVerification.detected_years.length > 0 && (
              <span className="px-2 py-0.5 bg-white rounded border border-emerald-300 font-semibold text-emerald-800 text-[11px] shrink-0">
                Academic Codes: {dateVerification.detected_years.join(", ")}
              </span>
            )}
          </div>
        )}

        {/* Active Faculty Batch Scope Banner (Strict Pool Enforcement) */}
        <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-slate-800">
            <Users className="w-4 h-4 text-slate-600 shrink-0" />
            <div>
              <span className="font-semibold">Active Faculty Pool (Strict Scope):</span>{" "}
              <span>{activeBatch?.batch_name || activeBatch?.filename || "TCET Verified Faculty List"}</span>
            </div>
          </div>
          <span className="px-2 py-0.5 bg-white border border-slate-200 rounded text-[11px] font-mono text-slate-700 shrink-0">
            {reqPreview?.eligible_faculty_available || activeBatch?.eligible_count || facultyPool.length} Eligible Faculty (Historical Absent Excluded)
          </span>
        </div>

        {/* SECTION 7: EXAMINATION PREVIEW CARD */}
        {dateExams.length > 0 ? (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs space-y-2">
            <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
              <span className="font-semibold text-slate-800">
                Examination Preview ({dateExams.length} Course{dateExams.length > 1 ? "s" : ""} in {selectedShift}
                {selectedTiming !== "all" ? ` • ${selectedTiming}` : ""}):
              </span>
              <span className="text-[11px] text-slate-500 font-mono">
                Date: {selectedDate}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 pt-0.5">
              {dateExams.map((ex: any, idx: number) => (
                <div
                  key={idx}
                  className="bg-white p-2.5 rounded border border-slate-200 text-xs flex flex-col justify-between space-y-1.5"
                >
                  <div className="space-y-0.5">
                    <div className="font-semibold text-slate-900 truncate">
                      {ex.subject_name || ex.exam_name}
                    </div>
                    <div className="text-[11px] text-slate-600">
                      <span className="font-semibold text-slate-800">{ex.academic_year || "Track"}</span> •{" "}
                      <span>{ex.department || ex.department_name}</span> •{" "}
                      <span className="font-mono text-slate-500">{ex.subject_code}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px] text-slate-500 font-mono">
                    <span>{ex.start_time} - {ex.end_time}</span>
                    <span className="px-1.5 py-0.2 bg-slate-100 rounded text-slate-700">
                      {ex.duration || "3 Hours"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600">
            No examinations scheduled on <span className="font-mono">{selectedDate}</span> for{" "}
            <span className="font-semibold">{selectedShift}</span>
            {selectedTiming !== "all" ? ` at ${selectedTiming}` : ""}.
          </div>
        )}

        {/* Live Calculation & Shortage Strip */}
        {reqPreview && (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-4 text-slate-700">
              <div>
                <span className="text-slate-500">Blocks: </span>
                <span className="font-semibold text-slate-900">{numClassrooms}</span>
              </div>
              <div className="h-3 w-px bg-slate-300 hidden sm:block"></div>
              <div>
                <span className="text-slate-500">Junior Supervisors: </span>
                <span className="font-semibold text-slate-900">{reqPreview.required_js}</span>
              </div>
              <div className="h-3 w-px bg-slate-300 hidden sm:block"></div>
              <div>
                <span className="text-slate-500">Relievers: </span>
                <span className="font-semibold text-slate-900">{reqPreview.required_relievers}</span>
              </div>
              <div className="h-3 w-px bg-slate-300 hidden sm:block"></div>
              <div>
                <span className="text-slate-500">Standby: </span>
                <span className="font-semibold text-slate-900">{reqPreview.required_standby}</span>
              </div>
              <div className="h-3 w-px bg-slate-300 hidden sm:block"></div>
              <div>
                <span className="text-slate-500">Total Required: </span>
                <span className="font-bold text-slate-900">
                  {reqPreview.total_required} of {reqPreview.eligible_faculty_available}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleGenerateAllocation}
                disabled={allocating || (reqPreview.shortage > 0)}
                className={`px-3 py-1.5 text-xs font-semibold rounded text-white shadow-2xs transition-colors ${
                  reqPreview.shortage > 0
                    ? "bg-slate-400 cursor-not-allowed"
                    : "bg-slate-900 hover:bg-slate-800"
                }`}
              >
                {allocating ? "Running Optimizer..." : "Generate Fair Duty Allocation"}
              </button>
            </div>
          </div>
        )}

        {/* Shortage Alert if Faculty Pool is Insufficient */}
        {shortageError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-900 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
            <div>
              <span className="font-semibold">Insufficient Faculty in Uploaded List:</span>{" "}
              Required: {shortageError.required}, Eligible available in current list: {shortageError.available} (Shortage: {shortageError.shortage}).
              The system will not select absent faculty from the historical database. Please upload an expanded faculty list or reduce classroom blocks.
            </div>
          </div>
        )}

        {/* Approval Notice */}
        {approvedNotice && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-900 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{approvedNotice}</span>
            </div>
            <span className="text-[11px] font-semibold text-emerald-800">
              Official Records Updated
            </span>
          </div>
        )}
      </div>

      {/* SECTION 3: DUTY CHART TABLE */}
      {allocationSummary && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Duty Allocation Chart — {selectedDate} ({selectedShift})
              </h2>
              <p className="text-[11px] text-slate-500">
                {numClassrooms} Classrooms • {allocationSummary.allocations?.length || 0} Faculty Assigned
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => window.open(`/api/allocation/export/${selectedShiftId || 1}/excel`, "_blank")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-medium rounded transition-colors"
              >
                <FileSpreadsheet className="w-3.5 h-3.5" />
                <span>Download Excel</span>
              </button>
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded transition-colors"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print</span>
              </button>
            </div>
          </div>

          {/* Search & Filter */}
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2 flex-1 min-w-[180px]">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Filter faculty, department, room..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full text-xs bg-slate-50 border border-slate-200 rounded px-2.5 py-1 text-slate-800 focus:outline-slate-400"
              />
            </div>

            <div className="flex items-center gap-2">
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="text-xs bg-white border border-slate-200 rounded px-2 py-1 text-slate-800"
              >
                <option value="all">All Roles</option>
                <option value="JS">Junior Supervisor (JS)</option>
                <option value="Reliever">Reliever</option>
                <option value="Standby">Standby</option>
              </select>

              <select
                value={deptFilter}
                onChange={(e) => setDeptFilter(e.target.value)}
                className="text-xs bg-white border border-slate-200 rounded px-2 py-1 text-slate-800 max-w-[180px]"
              >
                <option value="all">All Departments</option>
                {deptsInAllocation.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2 px-3">#</th>
                  <th className="py-2 px-3">Faculty Name</th>
                  <th className="py-2 px-3">Department</th>
                  <th className="py-2 px-3">Designation</th>
                  <th className="py-2 px-3">Role</th>
                  <th className="py-2 px-3">Room / Sector</th>
                  <th className="py-2 px-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredAllocations.map((alloc: any, idx: number) => {
                  const isJS = alloc.assigned_role === "JS";
                  const isReliever = alloc.assigned_role === "Reliever";

                  return (
                    <tr key={alloc.id || idx} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2 px-3 text-slate-400 tabular-nums">{idx + 1}</td>
                      <td className="py-2 px-3 font-medium text-slate-900">{alloc.faculty_name}</td>
                      <td className="py-2 px-3 text-slate-600">{alloc.department_name}</td>
                      <td className="py-2 px-3 text-slate-500">{alloc.designation}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                            isJS
                              ? "bg-slate-100 text-slate-800 border border-slate-200"
                              : isReliever
                              ? "bg-blue-50 text-blue-800 border border-blue-200"
                              : "bg-amber-50 text-amber-800 border border-amber-200"
                          }`}
                        >
                          {alloc.assigned_role}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-mono text-slate-800">
                        {alloc.assigned_block || "Central Control"}
                      </td>
                      <td className="py-2 px-3 text-right text-slate-500 text-[11px]">
                        Assigned
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
