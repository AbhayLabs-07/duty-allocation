"use client";

import React, { useState } from "react";
import { UserPlus, UploadCloud, CheckCircle2, AlertCircle, Edit2, Trash2, ArrowRight, Loader2, Info } from "lucide-react";
import { useRouter } from "next/navigation";

export default function FacultyListUploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [parsing, setParsing] = useState(false);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingCandidate, setEditingCandidate] = useState<any | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setCandidates([]);
      setSuccessMsg(null);
    }
  };

  const handleParse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a PDF, Excel, or CSV faculty list file.");
      return;
    }

    try {
      setParsing(true);
      setError(null);
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/faculty/upload/parse", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to parse faculty document.");
      }

      const data = await res.json();
      setCandidates(data.candidates);
      setParsing(false);
    } catch (err: any) {
      setError(err.message);
      setParsing(false);
    }
  };

  const handleEditCandidate = (c: any) => {
    setEditingCandidate({ ...c });
  };

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCandidate) return;
    setCandidates((prev) =>
      prev.map((item) =>
        item.faculty_id === editingCandidate.faculty_id ? editingCandidate : item
      )
    );
    setEditingCandidate(null);
  };

  const handleDeleteCandidate = (facId: string) => {
    setCandidates((prev) => prev.filter((item) => item.faculty_id !== facId));
  };

  const handleConfirmBatch = async () => {
    try {
      setConfirming(true);
      const res = await fetch("/api/faculty/upload/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(candidates),
      });
      const data = await res.json();
      setConfirming(false);
      setSuccessMsg(data.message);
    } catch (err: any) {
      alert("Failed to commit faculty list: " + err.message);
      setConfirming(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
          Upload Faculty List
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Upload faculty rosters via PDF, Excel, or CSV. Extracted faculty names, IDs, departments, and designations must be reviewed on this verification screen before saving to the permanent Faculty Master.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3.5 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Box */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-5">
        <form onSubmit={handleParse} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1">
              Select Faculty Document (PDF, Excel .xlsx/.xls, CSV)
            </label>
            <div className="border-2 border-dashed border-slate-200 hover:border-slate-300 rounded-lg p-6 text-center transition-colors">
              <input
                type="file"
                id="faculty-file"
                accept=".pdf,.xlsx,.xls,.csv"
                onChange={handleFileChange}
                className="hidden"
              />
              <label
                htmlFor="faculty-file"
                className="cursor-pointer flex flex-col items-center justify-center gap-2"
              >
                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div className="text-xs font-semibold text-slate-800">
                  {file ? file.name : "Click to select or drag and drop Faculty List document"}
                </div>
                <div className="text-[11px] text-slate-500">
                  Supported formats: PDF, Excel (.xlsx, .xls), CSV
                </div>
              </label>
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={parsing || !file}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
            >
              {parsing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Extracting Faculty Data...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  <span>Extract & Preview Faculty List</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {successMsg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs p-3.5 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button
            onClick={() => router.push("/faculty")}
            className="inline-flex items-center gap-1 font-semibold text-emerald-800 hover:text-emerald-950 underline"
          >
            <span>View Faculty Master</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Verification Screen */}
      {candidates.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden space-y-4 p-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                Extracted Faculty Verification Register
              </h2>
              <p className="text-xs text-slate-500">
                Review extracted records and OCR confidence scores before saving to the permanent Faculty Master.
              </p>
            </div>
            <button
              onClick={handleConfirmBatch}
              disabled={confirming}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{confirming ? "Saving..." : `Confirm & Save (${candidates.length}) Faculty`}</span>
            </button>
          </div>

          <div className="overflow-x-auto max-h-[450px]">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50/80 sticky top-0 border-b border-slate-200 text-slate-600 font-semibold z-10">
                <tr>
                  <th className="py-2.5 px-3.5 w-28">Faculty ID</th>
                  <th className="py-2.5 px-3.5">Faculty Full Name</th>
                  <th className="py-2.5 px-3.5 w-32">Department</th>
                  <th className="py-2.5 px-3.5 w-40">Designation</th>
                  <th className="py-2.5 px-3.5 w-28 text-center">Extraction Confidence</th>
                  <th className="py-2.5 px-3.5 w-20 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {candidates.map((c, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3.5 font-mono font-semibold text-slate-800">
                      {c.faculty_id}
                    </td>
                    <td className="py-2.5 px-3.5 font-bold text-slate-900">
                      {c.name}
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-700">
                      {c.department_name}
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-600">
                      {c.designation}
                    </td>
                    <td className="py-2.5 px-3.5 text-center">
                      <span className="font-mono font-bold text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 tabular-nums">
                        {c.confidence_score}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleEditCandidate(c)}
                          className="p-1 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded"
                          title="Edit Faculty"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteCandidate(c.faculty_id)}
                          className="p-1 text-slate-400 hover:text-red-700 hover:bg-red-50 rounded"
                          title="Delete Row"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Edit Candidate Modal */}
      {editingCandidate && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-5 border border-slate-200">
            <h3 className="text-sm font-bold text-slate-900 mb-3">
              Edit Faculty Candidate Entry
            </h3>
            <form onSubmit={handleSaveEdit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Faculty ID</label>
                <input
                  type="text"
                  required
                  value={editingCandidate.faculty_id}
                  onChange={(e) => setEditingCandidate({ ...editingCandidate, faculty_id: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Faculty Name</label>
                <input
                  type="text"
                  required
                  value={editingCandidate.name}
                  onChange={(e) => setEditingCandidate({ ...editingCandidate, name: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md font-semibold"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Department</label>
                <input
                  type="text"
                  required
                  value={editingCandidate.department_name}
                  onChange={(e) => setEditingCandidate({ ...editingCandidate, department_name: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Designation</label>
                <input
                  type="text"
                  required
                  value={editingCandidate.designation}
                  onChange={(e) => setEditingCandidate({ ...editingCandidate, designation: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingCandidate(null)}
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
    </div>
  );
}
