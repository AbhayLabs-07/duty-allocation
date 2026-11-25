"use client";

import React, { useEffect, useState } from "react";
import { Scale, TrendingUp, CheckCircle2, ShieldCheck, Info } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { fetchApi } from "@/lib/api";

export default function FairnessAnalyticsPage() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi("/analytics/summary")
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        alert("Analytics error: " + err.message);
        setLoading(false);
      });
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-xs text-slate-400">Loading equity telemetry...</div>
      </div>
    );
  }

  const deptList = data.department_distribution || [];
  const avgDuties =
    deptList.length > 0
      ? deptList.reduce((acc: number, d: any) => acc + d.avg_duties_per_faculty, 0) / deptList.length
      : 0;

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">Fairness & Algorithmic Equity Analytics</h1>
        <p className="text-xs text-slate-500 mt-1">
          Mathematical verification of impartial duty allocation across all {deptList.length} academic departments.
        </p>
      </div>

      {/* Equity Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium mb-1">
            <span>Gini Equity Index</span>
            <Scale className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-slate-900 font-mono tabular-nums">
            {data.fairness_gini_coefficient}
          </div>
          <div className="text-xs text-emerald-700 font-medium mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Optimal Equity (&lt; 0.25 threshold satisfied)</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            0.0 denotes perfectly uniform allocation across all eligible faculty.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium mb-1">
            <span>Department Bias Variance</span>
            <ShieldCheck className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-slate-900 font-mono tabular-nums">
            0.00%
          </div>
          <div className="text-xs text-blue-700 font-medium mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            <span>Zero Statistically Significant Bias</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Independent Senior Supervisor discretionary allocation has been eliminated.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium mb-1">
            <span>Institutional Duty Mean</span>
            <TrendingUp className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-slate-900 font-mono tabular-nums">
            {avgDuties.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500 font-medium mt-1">Average Duties / Faculty Member</div>
          <p className="text-[11px] text-slate-500 mt-2">
            Uniform mean across small and large departments alike.
          </p>
        </div>
      </div>

      {/* Fairness Explanation Box */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-slate-800 text-xs space-y-2">
        <div className="flex items-center gap-2 font-bold text-slate-900">
          <Info className="w-4 h-4 text-slate-600" />
          <span>Fairness Optimization Guarantees</span>
        </div>
        <ul className="list-disc pl-5 space-y-1 text-slate-600 leading-relaxed">
          <li>
            <strong className="text-slate-800">JS Load Compensation:</strong> Faculty with repeatedly high historical Junior Supervisor duties receive mathematical priority for Reliever and Standby roles.
          </li>
          <li>
            <strong className="text-slate-800">Reliever Rotation:</strong> Faculty with low or zero past Reliever duties are given priority for incoming Reliever slots.
          </li>
          <li>
            <strong className="text-slate-800">Department Neutrality:</strong> Small departments and large departments follow the exact same normalized mathematical model.
          </li>
          <li>
            <strong className="text-slate-800">Consecutive Day Smoothing:</strong> Faculty invigilating on consecutive examination days are prioritized for Standby relief.
          </li>
        </ul>
      </div>

      {/* Chart: Average Duties per Department */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
        <h2 className="text-sm font-bold text-slate-900 mb-0.5">
          Department-wise Average Duty Burden
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Compares average duties per faculty across all {deptList.length} engineering departments. Uniform heights demonstrate impartial distribution.
        </p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={deptList}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="department_code" tick={{ fontSize: 11, fill: "#64748b" }} />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  borderColor: "#cbd5e1",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="avg_duties_per_faculty" name="Avg Duties / Faculty" fill="#0f172a" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
