"use client";

import React, { useState, useEffect, Suspense } from "react";
import {
  FileCheck2,
  Search,
  Plus,
  Trash2,
  Edit2,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Filter,
} from "lucide-react";
import { useSearchParams, useRouter } from "next/navigation";

function TimetableReviewInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const uploadIdParam = searchParams.get("upload_id");

  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("all");
  const [editingRecord, setEditingRecord] = useState<any | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [confirmSuccess, setConfirmSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    exam_name: "End Semester Examination Winter 2026",
    department_name: "AI&DS",
    programme: "B.Tech Artificial Intelligence & Data Science",
    academic_year: "SE",
    semester: "Semester IV",
    subject_name: "",
    subject_code: "",
    exam_date: "2026-12-12",
    start_time: "10:30 AM",
    end_time: "01:30 PM",
  });

  const loadRecords = async () => {
    try {
      setLoading(true);
      const url = uploadIdParam
        ? `/api/timetables/records?upload_id=${uploadIdParam}`
        : `/api/timetables/records`;
      const res = await fetch(url);
      const data = await res.json();
      setRecords(data);
      setLoading(false);
    } catch (err: any) {
      alert("Failed to load extracted records: " + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, [uploadIdParam]);

  const handleOpenEdit = (rec: any) => {
    setEditingRecord(rec);
    setFormData({
      exam_name: rec.exam_name,
      department_name: rec.department_name,
      programme: rec.programme || "",
      academic_year: rec.academic_year,
      semester: rec.semester,
      subject_name: rec.subject_name,
      subject_code: rec.subject_code,
      exam_date: rec.exam_date,
      start_time: rec.start_time,
      end_time: rec.end_time,
    });
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRecord) return;
    try {
      const res = await fetch(`/api/timetables/records/${editingRecord.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error("Failed to save changes");
      setEditingRecord(null);
      loadRecords();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleAddRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/timetables/records`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          upload_id: uploadIdParam ? parseInt(uploadIdParam) : null,
        }),
      });
      if (!res.ok) throw new Error("Failed to add record");
      setAddModalOpen(false);
      loadRecords();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this candidate timetable row?")) return;
    try {
      await fetch(`/api/timetables/records/${id}`, { method: "DELETE" });
      loadRecords();
    } catch (err: any) {
      alert("Delete failed: " + err.message);
    }
  };

  const handleConfirmAll = async () => {
    try {
      setConfirming(true);
      const res = await fetch("/api/timetables/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          upload_id: uploadIdParam ? parseInt(uploadIdParam) : null,
        }),
      });
      const data = await res.json();
      setConfirming(false);
      setConfirmSuccess(data.message);
      loadRecords();
    } catch (err: any) {
      alert("Confirmation failed: " + err.message);
      setConfirming(false);
    }
  };

  const filtered = records.filter((r) => {
    const matchSearch =
      r.subject_name.toLowerCase().includes(search.toLowerCase()) ||
      r.subject_code.toLowerCase().includes(search.toLowerCase()) ||
      r.department_name.toLowerCase().includes(search.toLowerCase());
    const matchDept = selectedDept === "all" || r.department_name === selectedDept;
    return matchSearch && matchDept;
  });

  const uniqueDepts = Array.from(new Set<string>(records.map((r: any) => String(r.department_name))));
  const unconfirmedCount = records.filter((r) => !r.is_confirmed).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Review Extracted Timetable (OCR Review Screen)
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Human verification interface for document extraction. Edit errors, delete invalid rows, or confirm reviewed entries into the active Examination Database.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setFormData({
                exam_name: "End Semester Examination Winter 2026",
                department_name: "AI&DS",
                programme: "B.Tech AI&DS",
                academic_year: "SE",
                semester: "Semester IV",
                subject_name: "",
                subject_code: "",
                exam_date: "2026-12-12",
                start_time: "10:30 AM",
                end_time: "01:30 PM",
              });
              setAddModalOpen(true);
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold rounded-md shadow-2xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5 text-slate-500" />
            <span>Add Row</span>
          </button>

          <button
            onClick={handleConfirmAll}
            disabled={confirming || unconfirmedCount === 0}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>{confirming ? "Confirming..." : `Confirm All (${unconfirmedCount}) Records`}</span>
          </button>
        </div>
      </div>

      {confirmSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs p-3.5 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{confirmSuccess}</span>
          </div>
          <button
            onClick={() => router.push("/allocation")}
            className="inline-flex items-center gap-1 font-semibold text-emerald-800 hover:text-emerald-950 underline"
          >
            <span>Proceed to Create Duty Allocation</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-3 rounded-lg border border-slate-200 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by subject code, name, department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:bg-white focus:border-slate-400"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-600">
            <span>Department:</span>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2 py-1 font-medium text-slate-700 outline-none focus:border-slate-400"
            >
              <option value="all">All Departments</option>
              {uniqueDepts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="text-xs text-slate-500 tabular-nums">
            Showing <span className="font-semibold text-slate-900">{filtered.length}</span> of {records.length} entries
          </div>
        </div>
      </div>

      {/* Extracted Timetable Review Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3.5 w-28">Exam Date</th>
                <th className="py-2.5 px-3.5 w-24">Dept</th>
                <th className="py-2.5 px-3.5 w-16 text-center">Year</th>
                <th className="py-2.5 px-3.5 w-24">Code</th>
                <th className="py-2.5 px-3.5">Subject Name</th>
                <th className="py-2.5 px-3.5 w-36">Time Window</th>
                <th className="py-2.5 px-3.5 w-28 text-center">OCR Confidence</th>
                <th className="py-2.5 px-3.5 w-24 text-center">Status</th>
                <th className="py-2.5 px-3.5 w-20 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    Loading extracted timetable rows...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    No timetable records matching criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((r) => {
                  const isLowConfidence = r.confidence_score < 80;
                  return (
                    <tr
                      key={r.id}
                      className={`hover:bg-slate-50/70 transition-colors ${
                        isLowConfidence ? "bg-amber-50/40" : ""
                      }`}
                    >
                      <td className="py-2.5 px-3.5 font-mono text-slate-800 tabular-nums font-semibold">
                        {r.exam_date}
                      </td>
                      <td className="py-2.5 px-3.5">
                        <span className="font-mono font-bold text-slate-800 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded text-[10px]">
                          {r.department_name}
                        </span>
                      </td>
                      <td className="py-2.5 px-3.5 text-center font-mono font-bold text-slate-700">
                        {r.academic_year}
                      </td>
                      <td className="py-2.5 px-3.5 font-mono font-semibold text-slate-900">
                        {r.subject_code}
                      </td>
                      <td className="py-2.5 px-3.5 text-slate-800 font-medium">
                        <div>{r.subject_name}</div>
                        <div className="text-[10px] text-slate-400">{r.semester}</div>
                      </td>
                      <td className="py-2.5 px-3.5 font-mono text-slate-600 text-[11px] tabular-nums">
                        {r.time_range}
                      </td>
                      <td className="py-2.5 px-3.5 text-center">
                        <span
                          className={`inline-flex items-center gap-1 font-mono font-bold px-2 py-0.5 rounded text-[10px] border tabular-nums ${
                            r.confidence_score >= 90
                              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                              : isLowConfidence
                              ? "bg-amber-100 text-amber-900 border-amber-300 font-extrabold"
                              : "bg-blue-50 text-blue-800 border-blue-200"
                          }`}
                        >
                          {isLowConfidence && <AlertTriangle className="w-3 h-3 text-amber-700" />}
                          <span>{r.confidence_score}%</span>
                        </span>
                      </td>
                      <td className="py-2.5 px-3.5 text-center">
                        {r.is_confirmed ? (
                          <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                            Confirmed
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-500 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded">
                            Pending
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3.5 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleOpenEdit(r)}
                            className="p-1 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded"
                            title="Edit Record"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDelete(r.id)}
                            className="p-1 text-slate-400 hover:text-red-700 hover:bg-red-50 rounded"
                            title="Delete Row"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Record Modal */}
      {editingRecord && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-lg w-full p-5 border border-slate-200">
            <h3 className="text-sm font-bold text-slate-900 mb-3">
              Edit Extracted Timetable Record
            </h3>
            <form onSubmit={handleSaveEdit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Examination Date</label>
                  <input
                    type="date"
                    required
                    value={formData.exam_date}
                    onChange={(e) => setFormData({ ...formData, exam_date: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Department</label>
                  <input
                    type="text"
                    required
                    value={formData.department_name}
                    onChange={(e) => setFormData({ ...formData, department_name: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-semibold"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Academic Year Code</label>
                  <input
                    type="text"
                    required
                    value={formData.academic_year}
                    onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono uppercase"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Subject Code</label>
                  <input
                    type="text"
                    required
                    value={formData.subject_code}
                    onChange={(e) => setFormData({ ...formData, subject_code: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono uppercase font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Subject Name</label>
                <input
                  type="text"
                  required
                  value={formData.subject_name}
                  onChange={(e) => setFormData({ ...formData, subject_name: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Start Time</label>
                  <input
                    type="text"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">End Time</label>
                  <input
                    type="text"
                    required
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingRecord(null)}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md"
                >
                  Save Corrections
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Missing Record Modal */}
      {addModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-lg w-full p-5 border border-slate-200">
            <h3 className="text-sm font-bold text-slate-900 mb-3">
              Add Missing Timetable Entry
            </h3>
            <form onSubmit={handleAddRecord} className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Examination Date</label>
                  <input
                    type="date"
                    required
                    value={formData.exam_date}
                    onChange={(e) => setFormData({ ...formData, exam_date: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Department</label>
                  <input
                    type="text"
                    required
                    value={formData.department_name}
                    onChange={(e) => setFormData({ ...formData, department_name: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-semibold"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Academic Year Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SE, TE, BE"
                    value={formData.academic_year}
                    onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono uppercase"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Subject Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. AID301"
                    value={formData.subject_code}
                    onChange={(e) => setFormData({ ...formData, subject_code: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono uppercase font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Subject Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Database Management Systems"
                  value={formData.subject_name}
                  onChange={(e) => setFormData({ ...formData, subject_name: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Start Time</label>
                  <input
                    type="text"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">End Time</label>
                  <input
                    type="text"
                    required
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md"
                >
                  Add Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TimetableReviewPage() {
  return (
    <Suspense fallback={<div className="py-12 text-center text-xs text-slate-400">Loading timetable review...</div>}>
      <TimetableReviewInner />
    </Suspense>
  );
}
