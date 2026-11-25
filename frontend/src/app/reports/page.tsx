"use client";

import React, { useState, useEffect } from "react";
import {
  FileSpreadsheet,
  Download,
  Printer,
  Search,
} from "lucide-react";
import { fetchApi } from "@/lib/api";

const REPORTS = [
  { id: "1", code: "REP-01", name: "Daily Duty Allocation Report", desc: "Assigned duties for scheduled examination shifts" },
  { id: "2", code: "REP-02", name: "Faculty-wise Duty History", desc: "Chronological logs per faculty across all exams" },
  { id: "3", code: "REP-03", name: "Department-wise Duty Report", desc: "Department aggregates and equity ratios" },
  { id: "4", code: "REP-04", name: "JS Distribution Report", desc: "Classroom invigilation burden and frequency analysis" },
  { id: "5", code: "REP-05", name: "Reliever Distribution Report", desc: "Reliever assignment rotation and equity tracking" },
  { id: "6", code: "REP-06", name: "Standby Distribution Report", desc: "Reserve duty allotment across faculty members" },
  { id: "7", code: "REP-07", name: "Fairness Analysis Report", desc: "Algorithmic equity index and status per faculty" },
  { id: "8", code: "REP-08", name: "Manual Modification & Audit Report", desc: "Full audit trail of administrative overrides and approvals" },
];

export default function ReportsPage() {
  const [selectedReportId, setSelectedReportId] = useState("1");
  const [reportData, setReportData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  const loadReport = async (reportId: string) => {
    try {
      setLoading(true);
      const data = await fetchApi(`/reports/generate?report_type=${reportId}&format=json`);
      setReportData(data);
      setLoading(false);
    } catch (err: any) {
      alert("Error loading report: " + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport(selectedReportId);
  }, [selectedReportId]);

  const handleExport = (format: "excel" | "pdf" | "html") => {
    window.open(`/api/reports/generate?report_type=${selectedReportId}&format=${format}`, "_blank");
  };

  const filteredRows = reportData?.rows?.filter((r: any[]) =>
    r.some((cell) => String(cell || "").toLowerCase().includes(search.toLowerCase()))
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Official Examination Reports Center</h1>
          <p className="text-xs text-slate-500 mt-1">
            Download institutional compliance and fairness audit reports in Excel, PDF, or Printable HTML format.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport("excel")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold rounded-md transition-colors"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Excel (.xlsx)</span>
          </button>
          <button
            onClick={() => handleExport("pdf")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold rounded-md transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-red-600" />
            <span>PDF</span>
          </button>
          <button
            onClick={() => handleExport("html")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Printable HTML</span>
          </button>
        </div>
      </div>

      {/* Report Selector Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {REPORTS.map((rep) => {
          const isSelected = selectedReportId === rep.id;
          return (
            <button
              key={rep.id}
              onClick={() => setSelectedReportId(rep.id)}
              className={`text-left p-3 rounded-lg border transition-all ${
                isSelected
                  ? "bg-slate-900 text-white border-slate-900 shadow-2xs"
                  : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className={`font-mono text-[10px] font-bold px-1.5 py-0.2 rounded ${
                  isSelected ? "bg-slate-800 text-slate-200" : "bg-slate-100 text-slate-600"
                }`}>
                  {rep.code}
                </span>
              </div>
              <div className="font-semibold text-xs leading-snug mt-1.5">{rep.name}</div>
              <div className={`text-[11px] mt-0.5 line-clamp-1 ${isSelected ? "text-slate-300" : "text-slate-500"}`}>
                {rep.desc}
              </div>
            </button>
          );
        })}
      </div>

      {/* Report Content View */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs">
        <div className="p-3.5 border-b border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              {reportData?.title || "Report Preview"}
            </h2>
            <p className="text-xs text-slate-500 tabular-nums">
              Showing {filteredRows.length} records
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search in table..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-slate-400"
            />
          </div>
        </div>

        <div className="overflow-x-auto max-h-[550px]">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-100/80 sticky top-0 border-b border-slate-200 text-slate-700 font-semibold z-10">
              <tr>
                <th className="py-2.5 px-3.5 w-12 text-center">#</th>
                {reportData?.headers?.map((h: string, idx: number) => (
                  <th key={idx} className="py-2.5 px-3.5">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td
                    colSpan={(reportData?.headers?.length || 1) + 1}
                    className="py-12 text-center text-slate-400"
                  >
                    Generating report data...
                  </td>
                </tr>
              ) : filteredRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={(reportData?.headers?.length || 1) + 1}
                    className="py-12 text-center text-slate-400"
                  >
                    No records found for current report parameters.
                  </td>
                </tr>
              ) : (
                filteredRows.map((row: any[], rIdx: number) => (
                  <tr key={rIdx} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3.5 text-center text-slate-400 font-mono text-[11px] tabular-nums">
                      {rIdx + 1}
                    </td>
                    {row.map((cell: any, cIdx: number) => (
                      <td key={cIdx} className="py-2.5 px-3.5 text-slate-800">
                        {cell !== null && cell !== undefined ? String(cell) : "-"}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
