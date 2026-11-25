"use client";

import React, { useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, Loader2, Info } from "lucide-react";
import { useRouter } from "next/navigation";

export default function TimetableUploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [examName, setExamName] = useState("End Semester Examination Winter 2026");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select an examination timetable PDF file to upload.");
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("exam_name", examName);

      const res = await fetch("/api/timetables/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to process timetable document.");
      }

      const data = await res.json();
      setResult(data);
      setUploading(false);
    } catch (err: any) {
      setError(err.message);
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
          Upload Examination Timetable
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Upload official examination timetable PDFs (batch upload up to 150 pages supported). The system extracts exam dates, shifts, departments, academic levels (SE, TE, BE), subject codes, and names for human review.
        </p>
      </div>

      {/* Info notice on Academic Code Mapping */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 flex items-start gap-2.5 text-xs text-slate-600">
        <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">Dynamic Academic Code Mapping Active:</span>{" "}
          Abbreviations such as <span className="font-mono bg-white px-1.5 py-0.2 rounded border border-slate-200 text-slate-800">SE</span>,{" "}
          <span className="font-mono bg-white px-1.5 py-0.2 rounded border border-slate-200 text-slate-800">TE</span>,{" "}
          <span className="font-mono bg-white px-1.5 py-0.2 rounded border border-slate-200 text-slate-800">BE</span>,{" "}
          <span className="font-mono bg-white px-1.5 py-0.2 rounded border border-slate-200 text-slate-800">ST</span>,{" "}
          <span className="font-mono bg-white px-1.5 py-0.2 rounded border border-slate-200 text-slate-800">TT</span>,{" "}
          <span className="font-mono bg-white px-1.5 py-0.2 rounded border border-slate-200 text-slate-800">BT</span> are dynamically resolved via Admin Rules.
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3.5 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Form */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-5">
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1">
              Examination Session Name
            </label>
            <input
              type="text"
              required
              value={examName}
              onChange={(e) => setExamName(e.target.value)}
              className="w-full text-xs p-2.5 bg-slate-50 border border-slate-200 rounded-md font-medium text-slate-900 outline-none focus:bg-white focus:border-slate-400"
              placeholder="e.g. End Semester Examination Winter 2026"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1">
              Select Timetable PDF File
            </label>
            <div className="border-2 border-dashed border-slate-200 hover:border-slate-300 rounded-lg p-6 text-center transition-colors">
              <input
                type="file"
                id="timetable-file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
              />
              <label
                htmlFor="timetable-file"
                className="cursor-pointer flex flex-col items-center justify-center gap-2"
              >
                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <div className="text-xs font-semibold text-slate-800">
                  {file ? file.name : "Click to select or drag and drop Timetable PDF"}
                </div>
                <div className="text-[11px] text-slate-500">
                  Supported: Official Timetable PDF (scanned or native text) • Up to 150 pages
                </div>
              </label>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={uploading || !file}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing Extraction Pipeline...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  <span>Process Timetable & Extract</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Success Extraction Summary */}
      {result && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-emerald-950 space-y-3">
          <div className="flex items-center gap-2 font-bold text-xs text-emerald-900">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Document Extraction Completed Successfully</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs pt-1">
            <div className="bg-white/80 p-2.5 rounded border border-emerald-200/60">
              <span className="text-[10px] text-slate-500 block">Total Pages Processed</span>
              <span className="font-mono font-bold text-slate-900 text-sm tabular-nums">
                {result.total_pages} Pages
              </span>
            </div>
            <div className="bg-white/80 p-2.5 rounded border border-emerald-200/60">
              <span className="text-[10px] text-slate-500 block">Extracted Exam Records</span>
              <span className="font-mono font-bold text-emerald-800 text-sm tabular-nums">
                {result.records_count} Courses
              </span>
            </div>
            <div className="bg-white/80 p-2.5 rounded border border-emerald-200/60">
              <span className="text-[10px] text-slate-500 block">Review Status</span>
              <span className="font-semibold text-slate-800 text-xs">
                Pending Verification
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed">
            {result.message} As per institutional guidelines, extracted data must be reviewed and verified by the Controller of Examination before entering the active examination database.
          </p>

          <div className="pt-1 flex justify-end">
            <button
              onClick={() => router.push(`/timetables/review?upload_id=${result.upload_id}`)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
            >
              <span>Proceed to OCR Review Screen</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
