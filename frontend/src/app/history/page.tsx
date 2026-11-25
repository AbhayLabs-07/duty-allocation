"use client";

import React, { useState, useEffect } from "react";
import { History, Search, Filter, Calendar, Download } from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function FacultyDutyHistoryPage() {
  const [histories, setHistories] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("all");
  const [selectedRole, setSelectedRole] = useState("all");

  useEffect(() => {
    Promise.all([fetchApi("/history"), fetchApi("/departments")])
      .then(([hData, dData]) => {
        setHistories(hData);
        setDepartments(dData);
        setLoading(false);
      })
      .catch((err) => {
        alert("Error loading history: " + err.message);
        setLoading(false);
      });
  }, []);

  const filtered = histories.filter((h) => {
    const matchSearch =
      h.faculty_name.toLowerCase().includes(search.toLowerCase()) ||
      h.exam_name.toLowerCase().includes(search.toLowerCase());
    const matchDept = selectedDept === "all" || h.department_name === selectedDept;
    const matchRole = selectedRole === "all" || h.role_served === selectedRole;
    return matchSearch && matchDept && matchRole;
  });

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">Faculty Duty History Register</h1>
        <p className="text-xs text-slate-500 mt-1">
          Permanent date-wise duty logs across all examination sessions. Historical duty records are preserved permanently and never overwritten.
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white p-3.5 rounded-lg border border-slate-200 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search faculty name or exam..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-slate-400 focus:bg-white"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500">Department:</span>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 font-medium text-slate-700 outline-none focus:border-slate-400"
            >
              <option value="all">All Departments ({departments.length})</option>
              {departments.map((d) => (
                <option key={d.id} value={d.name}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500">Role Served:</span>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 font-medium text-slate-700 outline-none focus:border-slate-400"
            >
              <option value="all">All Roles</option>
              <option value="JS">Junior Supervisor (JS)</option>
              <option value="Reliever">Reliever</option>
              <option value="Standby">Standby</option>
              <option value="SS">Senior Supervisor (SS)</option>
            </select>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3.5 w-28">Date</th>
                <th className="py-2.5 px-3.5">Faculty Name</th>
                <th className="py-2.5 px-3.5">Department</th>
                <th className="py-2.5 px-3.5">Examination</th>
                <th className="py-2.5 px-3.5">Shift</th>
                <th className="py-2.5 px-3.5 text-center w-28">Role Served</th>
                <th className="py-2.5 px-3.5 w-32">Block / Room</th>
                <th className="py-2.5 px-3.5 text-center w-28">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    Loading duty history records...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No historical records matching criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3.5 font-mono text-slate-700 tabular-nums">{h.exam_date}</td>
                    <td className="py-2.5 px-3.5 font-semibold text-slate-900">{h.faculty_name}</td>
                    <td className="py-2.5 px-3.5 text-slate-600">{h.department_name}</td>
                    <td className="py-2.5 px-3.5 text-slate-700">{h.exam_name}</td>
                    <td className="py-2.5 px-3.5 text-slate-600">{h.shift_name}</td>
                    <td className="py-2.5 px-3.5 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          h.role_served === "JS"
                            ? "bg-slate-100 text-slate-800 border-slate-200"
                            : h.role_served === "Reliever"
                            ? "bg-blue-50 text-blue-800 border-blue-200"
                            : h.role_served === "Standby"
                            ? "bg-amber-50 text-amber-800 border-amber-200"
                            : "bg-purple-50 text-purple-800 border-purple-200"
                        }`}
                      >
                        {h.role_served}
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 font-mono text-slate-700">{h.block_or_room || "-"}</td>
                    <td className="py-2.5 px-3.5 text-center">
                      {h.is_manual_override ? (
                        <span className="text-[10px] bg-amber-50 text-amber-800 border border-amber-200 font-medium px-2 py-0.5 rounded">
                          Override
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-400">System</span>
                      )}
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
