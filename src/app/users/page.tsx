"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, UserCheck, History, Plus, AlertCircle, Clock } from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function UserManagementPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchApi("/users"), fetchApi("/users/audit-logs")])
      .then(([userData, logsData]) => {
        setUsers(userData);
        setAuditLogs(logsData);
        setLoading(false);
      })
      .catch((err) => {
        alert("Error loading users: " + err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">User Access & Governance Audit Logs</h1>
        <p className="text-xs text-slate-500 mt-1">
          Role-based access control (Super Admin, Examination Controller, HOD, Faculty). All manual duty modifications and policy updates are recorded permanently with caller identity.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Users List */}
        <div className="lg:col-span-1 bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-3">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900">Authorized Accounts</h2>
            <span className="text-xs font-mono font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded tabular-nums">
              {users.length} Users
            </span>
          </div>

          <div className="divide-y divide-slate-100 max-h-[500px] overflow-y-auto pr-1">
            {users.map((u) => (
              <div key={u.id} className="py-2.5 text-xs flex items-center justify-between">
                <div>
                  <div className="font-semibold text-slate-900">{u.full_name}</div>
                  <div className="text-[11px] text-slate-500 font-mono">@{u.username} • {u.email}</div>
                </div>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                    u.role === "Super Admin"
                      ? "bg-slate-900 text-white border-slate-900"
                      : u.role === "Examination Controller"
                      ? "bg-blue-50 text-blue-800 border-blue-200"
                      : u.role === "Department HOD"
                      ? "bg-purple-50 text-purple-800 border-purple-200"
                      : "bg-slate-100 text-slate-700 border-slate-200"
                  }`}
                >
                  {u.role}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Log Chronology */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-3">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Chronological Audit Log</h2>
              <p className="text-xs text-slate-500">Every administrative action, manual override, and allocation approval</p>
            </div>
            <History className="w-4 h-4 text-slate-400" />
          </div>

          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold sticky top-0">
                <tr>
                  <th className="py-2.5 px-3 w-40">Timestamp</th>
                  <th className="py-2.5 px-3 w-28">Action</th>
                  <th className="py-2.5 px-3 w-40">Authorized By</th>
                  <th className="py-2.5 px-3">Details / Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-400">
                      No audit events logged yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((l) => (
                    <tr key={l.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px] tabular-nums whitespace-nowrap">
                        {l.timestamp ? new Date(l.timestamp).toLocaleString() : "-"}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900">
                        <span className="bg-slate-100 border border-slate-200 text-slate-700 px-1.5 py-0.5 rounded text-[10px] font-mono">
                          {l.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-700">
                        <div className="font-medium text-slate-900">{l.performed_by}</div>
                        <div className="text-[10px] text-slate-400">{l.user_role}</div>
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 leading-relaxed text-[11px]">
                        {l.details}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
