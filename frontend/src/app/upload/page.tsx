"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  Check,
  Save,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function UploadDutyChartPage() {
  const [file, setFile] = useState<File | null>(null);
  const [examName, setExamName] = useState("");
  const [academicYear, setAcademicYear] = useState("2025-2026");
  const [semester, setSemester] = useState("Semester IV");
  const [uploading, setUploading] = useState(false);
  const [uploadedChart, setUploadedChart] = useState<any | null>(null);
  const [facultyMaster, setFacultyMaster] = useState<any[]>([]);

  const [records, setRecords] = useState<any[]>([]);
  const [savingVerification, setSavingVerification] = useState(false);
  const [verificationDone, setVerificationDone] = useState(false);

  useEffect(() => {
    fetchApi("/faculty").then((data) => setFacultyMaster(data)).catch(() => {});
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert("Please select a document file to upload.");
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append("file", file);
      if (examName) formData.append("exam_name", examName);
      if (academicYear) formData.append("exam_year", academicYear);
      if (semester) formData.append("semester", semester);

      const res = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      const chartData = await res.json();
      setUploadedChart(chartData);
      setRecords(chartData.extracted_records || []);
      setUploading(false);
    } catch (err: any) {
      alert("Upload & Parsing Error: " + err.message);
      setUploading(false);
    }
  };

  const handleUpdateRecord = async (recordId: number, matchedFacId: number, role: string) => {
    try {
      await fetchApi(`/documents/records/${recordId}`, {
        method: "PUT",
        body: JSON.stringify({
          id: recordId,
          matched_faculty_id: matchedFacId,
          verified_duty_role: role,
          is_verified: true,
          verification_notes: "Admin confirmed match",
        }),
      });

      setRecords((prev) =>
        prev.map((r) =>
          r.id === recordId
            ? { ...r, matched_faculty_id: matchedFacId, verified_duty_role: role, is_verified: true }
            : r
        )
      );
    } catch (err: any) {
      alert("Update failed: " + err.message);
    }
  };

  const handleVerifyAndCommit = async () => {
    if (!uploadedChart) return;
    try {
      setSavingVerification(true);
      const res = await fetchApi(`/documents/${uploadedChart.id}/verify-and-save`, {
        method: "POST",
      });
      setSavingVerification(false);
      setVerificationDone(true);
      alert(res.message);
    } catch (err: any) {
      alert("Verification commit error: " + err.message);
      setSavingVerification(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-slate-200">
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">
          Duty Chart Upload & Verification
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Process examination duty charts in Excel, Word (.docx), PDF, or scanned image formats.
          All extracted names are matched against the 368-faculty register for human verification before saving.
        </p>
      </div>

      {!uploadedChart && (
        <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-4">
          <form onSubmit={handleUpload} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Examination Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Second Year End-Sem Exam"
                  value={examName}
                  onChange={(e) => setExamName(e.target.value)}
                  className="w-full p-2 border border-slate-200 rounded outline-none"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Academic Year
                </label>
                <input
                  type="text"
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="w-full p-2 border border-slate-200 rounded outline-none"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Semester
                </label>
                <input
                  type="text"
                  value={semester}
                  onChange={(e) => setSemester(e.target.value)}
                  className="w-full p-2 border border-slate-200 rounded outline-none"
                />
              </div>
            </div>

            <div className="border border-dashed border-slate-300 rounded p-8 text-center bg-slate-50">
              <UploadCloud className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <div className="text-xs font-semibold text-slate-800">
                {file ? file.name : "Select duty chart file"}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Supported formats: Excel (.xlsx, .xls), Word (.docx), PDF (.pdf), and Images (.png, .jpg)
              </p>
              <input
                type="file"
                id="file_input"
                onChange={handleFileChange}
                accept=".xlsx,.xls,.docx,.pdf,.png,.jpg,.jpeg,.bmp"
                className="hidden"
              />
              <label
                htmlFor="file_input"
                className="mt-3 inline-block px-3.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded cursor-pointer transition-colors"
              >
                Browse File
              </label>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!file || uploading}
                className={`px-4 py-2 text-xs font-semibold rounded text-white transition-colors ${
                  !file || uploading ? "bg-slate-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {uploading ? "Extracting & Matching..." : "Upload & Process"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Verification View */}
      {uploadedChart && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div>
              <div className="font-bold text-slate-900 text-sm">
                Extracted Data Verification
              </div>
              <div className="text-slate-500 mt-0.5">
                File: {uploadedChart.filename} | {records.length} Extracted Faculty Entries
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setUploadedChart(null);
                  setFile(null);
                  setVerificationDone(false);
                }}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-medium"
              >
                Upload Different File
              </button>
              <button
                onClick={handleVerifyAndCommit}
                disabled={savingVerification || verificationDone}
                className={`px-3.5 py-1.5 font-semibold text-white rounded flex items-center gap-1.5 ${
                  verificationDone
                    ? "bg-emerald-600 cursor-default"
                    : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {verificationDone ? (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>Verified & Saved into History</span>
                  </>
                ) : savingVerification ? (
                  <span>Saving...</span>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Approve & Save Verified Records</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <div className="p-3 bg-slate-50 border-b border-slate-200 text-xs text-slate-600 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-slate-500 shrink-0" />
              <span>
                Verify matched faculty names and recognized duty roles. Correct any entries before committing to history.
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">#</th>
                    <th className="py-2.5 px-3">Raw Extracted Name</th>
                    <th className="py-2.5 px-3">Matched Faculty in Register</th>
                    <th className="py-2.5 px-3">Match Confidence</th>
                    <th className="py-2.5 px-3">Recognized Role</th>
                    <th className="py-2.5 px-3">Total Duty in Document</th>
                    <th className="py-2.5 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {records.map((r, idx) => (
                    <tr key={r.id} className="hover:bg-slate-50/70">
                      <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px] tabular-nums">
                        {idx + 1}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900">
                        {r.raw_faculty_name}
                        {r.raw_department && (
                          <span className="text-[10px] text-slate-500 block font-normal">
                            Dept: {r.raw_department}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <select
                          value={r.matched_faculty_id || ""}
                          onChange={(e) =>
                            handleUpdateRecord(
                              r.id,
                              parseInt(e.target.value),
                              r.verified_duty_role || r.raw_duty_role || "JS"
                            )
                          }
                          className="bg-white border border-slate-200 rounded p-1 text-xs text-slate-900 outline-none w-full max-w-xs"
                        >
                          <option value="">Select Matching Faculty</option>
                          {facultyMaster.map((fm) => (
                            <option key={fm.id} value={fm.id}>
                              {fm.name} ({fm.department_name})
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="py-2.5 px-3 font-mono tabular-nums">
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                            r.confidence_score >= 85
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-amber-50 text-amber-700"
                          }`}
                        >
                          {r.confidence_score}%
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <select
                          value={r.verified_duty_role || r.raw_duty_role || "JS"}
                          onChange={(e) =>
                            handleUpdateRecord(r.id, r.matched_faculty_id, e.target.value)
                          }
                          className="bg-white border border-slate-200 rounded p-1 text-xs font-semibold outline-none"
                        >
                          <option value="JS">Junior Supervisor (JS)</option>
                          <option value="Reliever">Reliever</option>
                          <option value="Standby">Standby</option>
                          <option value="SS">Senior Supervisor (SS)</option>
                        </select>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-700 tabular-nums">
                        {r.raw_total_duty !== null ? `${r.raw_total_duty}` : "-"}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {r.is_verified ? (
                          <span className="text-[11px] text-emerald-700 font-medium">
                            Verified
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400">Review</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
