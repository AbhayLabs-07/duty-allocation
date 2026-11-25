"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  Plus,
  Trash2,
  Edit2,
  Save,
  CheckCircle2,
  Sliders,
  ShieldAlert,
  Info,
} from "lucide-react";

export default function SystemRulesPage() {
  const [mappings, setMappings] = useState<any[]>([]);
  const [rules, setRules] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingRules, setSavingRules] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState<string | null>(null);

  // Mapping Form Modal State
  const [mappingModalOpen, setMappingModalOpen] = useState(false);
  const [mappingFormData, setMappingFormData] = useState({
    code: "",
    full_name: "",
    category: "Year",
    description: "",
  });

  const loadAll = async () => {
    try {
      setLoading(true);
      const [mRes, rRes] = await Promise.all([
        fetch("/api/timetables/mappings"),
        fetch("/api/rules"),
      ]);
      const mData = await mRes.json();
      const rData = await rRes.json();
      setMappings(mData);
      setRules(rData);
      setLoading(false);
    } catch (err: any) {
      alert("Failed to load rules: " + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleSaveRules = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rules) return;
    try {
      setSavingRules(true);
      const res = await fetch("/api/rules", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rules),
      });
      if (!res.ok) throw new Error("Failed to update rules");
      setSavingRules(false);
      setSavedSuccess("System rules and conflict policies successfully saved and logged.");
      setTimeout(() => setSavedSuccess(null), 4000);
    } catch (err: any) {
      alert(err.message);
      setSavingRules(false);
    }
  };

  const handleSaveMapping = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/timetables/mappings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mappingFormData),
      });
      if (!res.ok) throw new Error("Failed to save mapping");
      setMappingModalOpen(false);
      setMappingFormData({ code: "", full_name: "", category: "Year", description: "" });
      loadAll();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDeleteMapping = async (id: number) => {
    if (!confirm("Delete this academic code mapping?")) return;
    try {
      await fetch(`/api/timetables/mappings/${id}`, { method: "DELETE" });
      loadAll();
    } catch (err: any) {
      alert("Delete failed: " + err.message);
    }
  };

  if (loading || !rules) {
    return <div className="py-12 text-center text-slate-400">Loading system rules...</div>;
  }

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
          System Rules & Academic Code Mappings
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure institutional staffing rules, same-department conflict policies, and academic terminology code mappings.
        </p>
      </div>

      {savedSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs p-3.5 rounded-md flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{savedSuccess}</span>
        </div>
      )}

      {/* SECTION 1: Academic Code Mapping (Section 2 of requirements) */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-5 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-blue-600" />
              <span>Academic Code Mapping (Terminology Adaptability)</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Defines how timetable abbreviations (SE, TE, BE, ST, TT, BT) map to official academic year and programme titles.
            </p>
          </div>
          <button
            onClick={() => setMappingModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Code Mapping</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3.5 w-24">Code</th>
                <th className="py-2.5 px-3.5 w-64">Full Academic Year / Programme Name</th>
                <th className="py-2.5 px-3.5 w-32">Category</th>
                <th className="py-2.5 px-3.5">Institutional Description</th>
                <th className="py-2.5 px-3.5 w-16 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mappings.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-2.5 px-3.5">
                    <span className="font-mono font-bold text-slate-900 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-[11px]">
                      {m.code}
                    </span>
                  </td>
                  <td className="py-2.5 px-3.5 font-semibold text-slate-900">
                    {m.full_name}
                  </td>
                  <td className="py-2.5 px-3.5 text-slate-600 font-medium">
                    {m.category}
                  </td>
                  <td className="py-2.5 px-3.5 text-slate-500 text-[11px]">
                    {m.description || "—"}
                  </td>
                  <td className="py-2.5 px-3.5 text-right">
                    <button
                      onClick={() => handleDeleteMapping(m.id)}
                      className="p-1 text-slate-400 hover:text-red-700 hover:bg-red-50 rounded"
                      title="Delete Mapping"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* SECTION 2: Staffing Rules & Conflict Rules Form (Section 6, 11 of requirements) */}
      <form onSubmit={handleSaveRules} className="space-y-6">
        {/* Staffing Ratio Configuration */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-5 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Sliders className="w-4 h-4 text-slate-600" />
            <span>Classroom Staffing Ratios (Dynamic Role Calculation)</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Junior Supervisors per Classroom
              </label>
              <select
                value={rules.js_per_classroom || 1}
                onChange={(e) => setRules({ ...rules, js_per_classroom: parseInt(e.target.value) || 1 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400"
              >
                <option value={1}>1 Junior Supervisor per Classroom</option>
                <option value={2}>2 Junior Supervisors per Classroom (Dual Invigilation)</option>
              </select>
              <p className="text-[11px] text-slate-500 mt-1">
                Controls JS positions: Total JS = Classrooms × Supervisors.
              </p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Reliever Ratio (Classrooms per Reliever)
              </label>
              <input
                type="number"
                min="1"
                max="12"
                value={rules.reliever_ratio}
                onChange={(e) => setRules({ ...rules, reliever_ratio: parseInt(e.target.value) || 1 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                e.g. 4 means 1 Reliever for every 4 examination blocks.
              </p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Standby Reserve Floor Count
              </label>
              <input
                type="number"
                min="1"
                max="30"
                value={rules.standby_ratio_or_count}
                onChange={(e) => setRules({ ...rules, standby_ratio_or_count: parseInt(e.target.value) || 1 })}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Minimum emergency reserve personnel stationed at Examination Control.
              </p>
            </div>
          </div>
        </div>

        {/* Conflict Policies (Section 11) */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-5 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Configurable Examination Conflict Rules</span>
          </h2>

          <div className="space-y-3 text-xs">
            <label className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/50 cursor-pointer hover:bg-slate-50 transition-colors">
              <input
                type="checkbox"
                checked={rules.disallow_same_department_js}
                onChange={(e) => setRules({ ...rules, disallow_same_department_js: e.target.checked })}
                className="rounded border-slate-300 text-slate-900 focus:ring-slate-500 w-4 h-4 mt-0.5"
              />
              <div>
                <span className="font-bold text-slate-900 block">
                  Disallow Same-Department Classroom Invigilation
                </span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  When enabled, faculty members will NOT be assigned as Junior Supervisors for examinations belonging to their own department (e.g. AI&DS faculty cannot invigilate AI&DS exam sessions).
                </span>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/50 cursor-pointer hover:bg-slate-50 transition-colors">
              <input
                type="checkbox"
                checked={rules.disallow_same_subject_js}
                onChange={(e) => setRules({ ...rules, disallow_same_subject_js: e.target.checked })}
                className="rounded border-slate-300 text-slate-900 focus:ring-slate-500 w-4 h-4 mt-0.5"
              />
              <div>
                <span className="font-bold text-slate-900 block">
                  Disallow Same-Subject Teaching Faculty
                </span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  Enforces strict examination integrity by preventing faculty from supervising subjects they teach.
                </span>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/50 cursor-pointer hover:bg-slate-50 transition-colors">
              <input
                type="checkbox"
                checked={rules.exclude_ss_from_fairness}
                onChange={(e) => setRules({ ...rules, exclude_ss_from_fairness: e.target.checked })}
                className="rounded border-slate-300 text-slate-900 focus:ring-slate-500 w-4 h-4 mt-0.5"
              />
              <div>
                <span className="font-bold text-slate-900 block">
                  Exclude Institutional Leadership (HOD / Deans) from Invigilation Pool
                </span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  HODs and Deans are assigned to Senior Supervisor (SS) tracking and excluded from the regular JS/Reliever/Standby pool.
                </span>
              </div>
            </label>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={savingRules}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white font-semibold text-xs rounded-md shadow-2xs transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>{savingRules ? "Saving Rules..." : "Save System Rules & Conflict Policies"}</span>
          </button>
        </div>
      </form>

      {/* Add Mapping Modal */}
      {mappingModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-5 border border-slate-200">
            <h3 className="text-sm font-bold text-slate-900 mb-3">
              Add Academic Code Mapping
            </h3>
            <form onSubmit={handleSaveMapping} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Abbreviation / Code
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ST, TT, BT, ME"
                  value={mappingFormData.code}
                  onChange={(e) => setMappingFormData({ ...mappingFormData, code: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md font-mono uppercase font-bold"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Full Academic Year / Programme Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Second Year (Autonomous Track)"
                  value={mappingFormData.full_name}
                  onChange={(e) => setMappingFormData({ ...mappingFormData, full_name: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Category
                </label>
                <select
                  value={mappingFormData.category}
                  onChange={(e) => setMappingFormData({ ...mappingFormData, category: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md"
                >
                  <option value="Year">Academic Year</option>
                  <option value="Programme">Programme / Track</option>
                  <option value="Shift">Examination Shift</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Institutional Description (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Used for autonomous batch timetables"
                  value={mappingFormData.description}
                  onChange={(e) => setMappingFormData({ ...mappingFormData, description: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md text-slate-700"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setMappingModalOpen(false)}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md"
                >
                  Save Mapping
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
