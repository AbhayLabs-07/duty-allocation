"use client";

import React, { useState, useEffect } from "react";
import { CalendarCheck, Search, Filter, Calendar, Clock, BookOpen, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export default function TimetableRecordsPage() {
  const router = useRouter();
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDate, setSelectedDate] = useState("all");

  useEffect(() => {
    fetch("/api/timetables/records?is_confirmed=true")
      .then((res) => res.json())
      .then((data) => {
        setRecords(data);
        setLoading(false);
      })
      .catch((err) => {
        alert("Failed to load confirmed timetable records: " + err.message);
        setLoading(false);
      });
  }, []);

  const datesList = Array.from(new Set<string>(records.map((r: any) => String(r.exam_date))));

  const filtered = records.filter((r) => {
    const matchSearch =
      r.subject_name.toLowerCase().includes(search.toLowerCase()) ||
      r.subject_code.toLowerCase().includes(search.toLowerCase()) ||
      r.department_name.toLowerCase().includes(search.toLowerCase());
    const matchDate = selectedDate === "all" || r.exam_date === selectedDate;
    return matchSearch && matchDate;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Confirmed Examination Timetable Records
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Official confirmed examination schedules verified by the Controller of Examination. Ready for classroom block allocation.
          </p>
        </div>

        <button
          onClick={() => router.push("/allocation")}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
        >
          <span>Create Duty Allocation</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

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
            <span>Exam Date:</span>
            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2 py-1 font-medium text-slate-700 outline-none focus:border-slate-400"
            >
              <option value="all">All Dates ({datesList.length})</option>
              {datesList.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="text-xs text-slate-500 tabular-nums">
            Showing <span className="font-semibold text-slate-900">{filtered.length}</span> verified courses
          </div>
        </div>
      </div>

      {/* Records Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3.5 w-32">Date</th>
                <th className="py-2.5 px-3.5 w-24">Dept</th>
                <th className="py-2.5 px-3.5 w-16 text-center">Year</th>
                <th className="py-2.5 px-3.5 w-24">Subject Code</th>
                <th className="py-2.5 px-3.5">Course / Subject Name</th>
                <th className="py-2.5 px-3.5 w-36">Time Window</th>
                <th className="py-2.5 px-3.5 w-24 text-center">Status</th>
                <th className="py-2.5 px-3.5 w-28 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    Loading verified timetable records...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No confirmed timetable records found. Please review and confirm records in the OCR Review Screen.
                  </td>
                </tr>
              ) : (
                filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 px-3.5 font-mono text-slate-800 font-bold tabular-nums">
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
                      <div className="text-[10px] text-slate-400">{r.programme} • {r.semester}</div>
                    </td>
                    <td className="py-2.5 px-3.5 font-mono text-slate-600 text-[11px] tabular-nums">
                      {r.time_range}
                    </td>
                    <td className="py-2.5 px-3.5 text-center">
                      <span className="inline-block px-2 py-0.5 text-[10px] font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 rounded">
                        Active Database
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 text-right">
                      <button
                        onClick={() => router.push(`/allocation?date=${r.exam_date}`)}
                        className="text-xs font-semibold text-slate-800 hover:text-slate-950 underline"
                      >
                        Allocate Duties
                      </button>
                    </td>
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
