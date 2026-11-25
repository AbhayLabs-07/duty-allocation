"use client";

import React, { useState, useEffect } from "react";
import { Sliders, Save, CheckCircle2, ShieldCheck, Scale } from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function SettingsPage() {
  const [config, setConfig] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    fetchApi("/settings/fairness-config")
      .then((data) => {
        setConfig(data);
        setLoading(false);
      })
      .catch((err) => {
        alert("Error loading settings: " + err.message);
        setLoading(false);
      });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;
    try {
      setSaving(true);
      setSavedSuccess(false);
      await fetchApi("/settings/fairness-config", {
        method: "PUT",
        body: JSON.stringify({
          reliever_ratio: Number(config.reliever_ratio),
          weight_prev_js: Number(config.weight_prev_js),
          weight_prev_reliever: Number(config.weight_prev_reliever),
          weight_prev_standby: Number(config.weight_prev_standby),
          weight_consecutive: Number(config.weight_consecutive),
          weight_dept_equity: Number(config.weight_dept_equity),
          exclude_ss_from_fairness: Boolean(config.exclude_ss_from_fairness),
        }),
      });
      setSaving(false);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: any) {
      alert("Failed to save settings: " + err.message);
      setSaving(false);
    }
  };

  if (loading || !config) {
    return <div className="py-12 text-center text-slate-400">Loading optimization settings...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">Fairness Policy & Optimization Parameters</h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure mathematical constraints and solver objective weights for Google OR-Tools CP-SAT.
        </p>
      </div>

      {savedSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-md p-3 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span className="font-semibold">Fairness optimization parameters saved and logged to audit trail.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-5">
        {/* Coverage Ratios */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-3.5">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-600" />
            <span>Classroom & Reliever Coverage Rules</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Reliever Ratio (Classrooms per Reliever)
              </label>
              <input
                type="number"
                min="1"
                max="12"
                value={config.reliever_ratio}
                onChange={(e) => setConfig({ ...config, reliever_ratio: parseInt(e.target.value) || 1 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                e.g. 4 means 1 Reliever covers 4 examination classrooms (e.g. 8 relievers for 32 blocks).
              </p>
            </div>

            <div className="flex flex-col justify-center">
              <label className="flex items-center gap-2 cursor-pointer pt-2">
                <input
                  type="checkbox"
                  checked={config.exclude_ss_from_fairness}
                  onChange={(e) => setConfig({ ...config, exclude_ss_from_fairness: e.target.checked })}
                  className="rounded border-slate-300 text-slate-900 focus:ring-slate-500 w-4 h-4"
                />
                <span className="font-semibold text-slate-800 text-xs">
                  Exclude Senior Supervisors (HOD / Dy. HOD) from JS/Reliever pool
                </span>
              </label>
              <p className="text-[11px] text-slate-500 mt-1 pl-6">
                Institutional leaders (Principal, Deans, HODs) are assigned to Senior Supervisor (SS) tracking.
              </p>
            </div>
          </div>
        </div>

        {/* Solver Cost Weights */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-2xs space-y-3.5">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Scale className="w-4 h-4 text-slate-600" />
            <span>Google OR-Tools Optimization Objective Weights</span>
          </h2>
          <p className="text-xs text-slate-500">
            Higher weights increase mathematical priority for balancing that specific duty dimension during constraint solving.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Previous JS Burden Penalty Weight (W_JS)
              </label>
              <input
                type="number"
                step="0.1"
                value={config.weight_prev_js}
                onChange={(e) => setConfig({ ...config, weight_prev_js: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Penalizes assigning JS to faculty who have repeatedly served as Junior Supervisors.
              </p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Reliever Rotation Incentive Weight (W_Reliever)
              </label>
              <input
                type="number"
                step="0.1"
                value={config.weight_prev_reliever}
                onChange={(e) => setConfig({ ...config, weight_prev_reliever: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Prioritizes faculty with zero or fewer Reliever opportunities.
              </p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Standby Rotation Incentive Weight (W_Standby)
              </label>
              <input
                type="number"
                step="0.1"
                value={config.weight_prev_standby}
                onChange={(e) => setConfig({ ...config, weight_prev_standby: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Rotates Standby reserve role across faculty fairly.
              </p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Consecutive Duty Relief Weight (W_Consecutive)
              </label>
              <input
                type="number"
                step="0.1"
                value={config.weight_consecutive}
                onChange={(e) => setConfig({ ...config, weight_consecutive: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Prevents back-to-back classroom duty fatigue.
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-md shadow-sm transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? "Saving..." : "Save Configuration"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
