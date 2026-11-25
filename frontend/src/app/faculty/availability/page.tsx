"use client";

import React, { useState, useEffect } from "react";
import { UserCheck, Search, Calendar, CheckCircle2, AlertCircle, Save, Filter } from "lucide-react";

const STATUS_OPTIONS = [
  { value: "Available", label: "Available", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  { value: "On Leave", label: "On Leave", color: "text-red-700 bg-red-50 border-red-200" },
  { value: "Unavailable", label: "Unavailable", color: "text-amber-700 bg-amber-50 border-amber-200" },
  { value: "Official Duty", label: "Official Duty", color: "text-blue-700 bg-blue-50 border-blue-200" },
  { value: "Exempted", label: "Exempted", color: "text-purple-700 bg-purple-50 border-purple-200" },
  { value: "Other", label: "Other", color: "text-slate-700 bg-slate-100 border-slate-200" },
];

export default function FacultyAvailabilityPage() {
  const [selectedDate, setSelectedDate] = useState("2026-12-12");
  const [availabilityList, setAvailabilityList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("all");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [savedSuccess, setSavedSuccess] = useState<string | null>(null);

  const loadAvailability = async (dStr: string) => {
    try {
      setLoading(true);
      const res = await fetch(`/api/faculty/availability/list?date=${dStr}`);
      if (!res.ok) throw new Error("Failed to load availability records");
      const data = await res.json();
      setAvailabilityList(data);
      setLoading(false);
    } catch (err: any) {
      alert(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAvailability(selectedDate);
  }, [selectedDate]);

  const handleStatusChange = (facultyId: number, newStatus: string) => {
    setAvailabilityList((prev) =>
      prev.map((item) =>
        item.faculty_id === facultyId
          ? { ...item, status: newStatus, is_available: newStatus === "Available" }
          : item
      )
    );
  };

  const handleReasonChange = (facultyId: number, newReason: string) => {
    setAvailabilityList((prev) =>
      prev.map((item) =>
        item.faculty_id === facultyId ? { ...item, reason: newReason } : item
      )
    );
  };

  const handleSaveIndividual = async (item: any) => {
    try {
      setSavingId(item.faculty_id);
      const res = await fetch("/api/faculty/availability", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          faculty_id: item.faculty_id,
          date: selectedDate,
          status: item.status,
          reason: item.reason,
          recorded_by: "Controller of Examination",
        }),
      });
      if (!res.ok) throw new Error("Failed to save status");
      setSavingId(null);
      setSavedSuccess(`Updated ${item.name} to '${item.status}'`);
      setTimeout(() => setSavedSuccess(null), 3000);
    } catch (err: any) {
      alert(err.message);
      setSavingId(null);
    }
  };

  const filtered = availabilityList.filter((item) => {
    const matchSearch =
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.code.toLowerCase().includes(search.toLowerCase()) ||
      item.department_name.toLowerCase().includes(search.toLowerCase());
    const matchDept = selectedDept === "all" || item.department_name === selectedDept;
    return matchSearch && matchDept;
  });

  const depts = Array.from(new Set<string>(availabilityList.map((a: any) => String(a.department_name))));
  const unavailableCount = availabilityList.filter((a) => a.status !== "Available").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Faculty Availability & Exclusions
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Mark faculty members as On Leave, Official Duty, or Exempted for specific examination dates. Unavailable faculty are enforced as a Hard Constraint and blocked from the allocation pool.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-700">Exam Date:</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="text-xs font-mono font-semibold p-1.5 bg-white border border-slate-300 rounded-md outline-none focus:border-slate-500"
          />
        </div>
      </div>

      {savedSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs p-3 rounded-md flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{savedSuccess}</span>
        </div>
      )}

      {/* Summary Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
          <span className="text-[10px] text-slate-500 block">Total Active Roster</span>
          <span className="font-mono font-bold text-slate-900 text-base tabular-nums">
            {availabilityList.length} Faculty
          </span>
        </div>
        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
          <span className="text-[10px] text-slate-500 block">Available Invigilators</span>
          <span className="font-mono font-bold text-emerald-700 text-base tabular-nums">
            {availabilityList.length - unavailableCount} Faculty
          </span>
        </div>
        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
          <span className="text-[10px] text-slate-500 block">Exclusions / On Leave</span>
          <span className="font-mono font-bold text-red-700 text-base tabular-nums">
            {unavailableCount} Faculty
          </span>
        </div>
        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
          <span className="text-[10px] text-slate-500 block">Constraint Mode</span>
          <span className="font-semibold text-slate-800 text-xs">
            Hard Constraint Active
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-3 rounded-lg border border-slate-200 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search faculty name, ID, or department..."
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
              {depts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="text-xs text-slate-500 tabular-nums">
            Showing <span className="font-semibold text-slate-900">{filtered.length}</span> faculty members
          </div>
        </div>
      </div>

      {/* Availability Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3.5 w-24">Faculty ID</th>
                <th className="py-2.5 px-3.5">Faculty Name</th>
                <th className="py-2.5 px-3.5 w-32">Department</th>
                <th className="py-2.5 px-3.5 w-36">Designation</th>
                <th className="py-2.5 px-3.5 w-36">Availability Status</th>
                <th className="py-2.5 px-3.5">Reason for Exclusion</th>
                <th className="py-2.5 px-3.5 w-20 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    Loading faculty availability matrix...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No faculty found matching search filters.
                  </td>
                </tr>
              ) : (
                filtered.map((item) => (
                  <tr key={item.faculty_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3.5 font-mono text-slate-700 font-semibold">
                      {item.code}
                    </td>
                    <td className="py-2.5 px-3.5 font-bold text-slate-900">
                      {item.name}
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-700">
                      {item.department_name}
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-500 text-[11px]">
                      {item.designation}
                    </td>
                    <td className="py-2.5 px-3.5">
                      <select
                        value={item.status}
                        onChange={(e) => handleStatusChange(item.faculty_id, e.target.value)}
                        className={`text-xs font-semibold px-2 py-1 rounded border outline-none ${
                          STATUS_OPTIONS.find((s) => s.value === item.status)?.color || ""
                        }`}
                      >
                        {STATUS_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2.5 px-3.5">
                      <input
                        type="text"
                        placeholder={item.status !== "Available" ? "Enter exclusion reason..." : "Optional notes"}
                        value={item.reason || ""}
                        onChange={(e) => handleReasonChange(item.faculty_id, e.target.value)}
                        className="w-full text-xs p-1.5 bg-slate-50 border border-slate-200 rounded text-slate-800 placeholder:text-slate-400 outline-none focus:bg-white focus:border-slate-400"
                      />
                    </td>
                    <td className="py-2.5 px-3.5 text-right">
                      <button
                        onClick={() => handleSaveIndividual(item)}
                        disabled={savingId === item.faculty_id}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded text-[11px] font-semibold transition-colors disabled:bg-slate-400"
                      >
                        <Save className="w-3 h-3" />
                        <span>{savingId === item.faculty_id ? "Saving..." : "Save"}</span>
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
