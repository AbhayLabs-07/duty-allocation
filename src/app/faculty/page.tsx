"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  Users,
  Search,
  Plus,
  Download,
  Upload,
  Edit2,
  Trash2,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function FacultyManagementPage() {
  const [faculty, setFaculty] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState<string>("all");
  const [selectedRole, setSelectedRole] = useState<string>("all");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState<any | null>(null);
  const [formData, setFormData] = useState({
    faculty_id: "",
    name: "",
    department_id: "",
    designation: "Assistant Professor",
    role_category: "Faculty",
    employment_status: "Regular",
    eligibility: true,
    previous_js_count: 0,
    previous_reliever_count: 0,
    previous_standby_count: 0,
    previous_ss_count: 0,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [facData, deptData] = await Promise.all([
        fetchApi("/faculty"),
        fetchApi("/departments"),
      ]);
      setFaculty(facData);
      setDepartments(deptData);
      setLoading(false);
    } catch (err: any) {
      alert("Error loading faculty: " + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredFaculty = useMemo(() => {
    return faculty.filter((f) => {
      const matchSearch =
        f.name.toLowerCase().includes(search.toLowerCase()) ||
        f.faculty_id.toLowerCase().includes(search.toLowerCase()) ||
        f.designation.toLowerCase().includes(search.toLowerCase());
      const matchDept = selectedDept === "all" || String(f.department_id) === selectedDept;
      const matchRole = selectedRole === "all" || f.role_category === selectedRole;
      return matchSearch && matchDept && matchRole;
    });
  }, [faculty, search, selectedDept, selectedRole]);

  const handleOpenAdd = () => {
    setEditingFaculty(null);
    setFormData({
      faculty_id: `TCET-FAC-${Math.floor(1000 + Math.random() * 9000)}`,
      name: "",
      department_id: departments[0]?.id ? String(departments[0].id) : "1",
      designation: "Assistant Professor",
      role_category: "Faculty",
      employment_status: "Regular",
      eligibility: true,
      previous_js_count: 0,
      previous_reliever_count: 0,
      previous_standby_count: 0,
      previous_ss_count: 0,
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (f: any) => {
    setEditingFaculty(f);
    setFormData({
      faculty_id: f.faculty_id,
      name: f.name,
      department_id: String(f.department_id),
      designation: f.designation,
      role_category: f.role_category,
      employment_status: f.employment_status,
      eligibility: f.eligibility,
      previous_js_count: f.previous_js_count,
      previous_reliever_count: f.previous_reliever_count,
      previous_standby_count: f.previous_standby_count,
      previous_ss_count: f.previous_ss_count,
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Are you sure you want to remove faculty "${name}"?`)) return;
    try {
      await fetchApi(`/faculty/${id}`, { method: "DELETE" });
      loadData();
    } catch (err: any) {
      alert("Delete failed: " + err.message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingFaculty) {
        await fetchApi(`/faculty/${editingFaculty.id}`, {
          method: "PUT",
          body: JSON.stringify({
            name: formData.name,
            department_id: parseInt(formData.department_id),
            designation: formData.designation,
            role_category: formData.role_category,
            employment_status: formData.employment_status,
            eligibility: formData.eligibility,
            previous_js_count: Number(formData.previous_js_count),
            previous_reliever_count: Number(formData.previous_reliever_count),
            previous_standby_count: Number(formData.previous_standby_count),
            previous_ss_count: Number(formData.previous_ss_count),
          }),
        });
      } else {
        await fetchApi("/faculty", {
          method: "POST",
          body: JSON.stringify({
            faculty_id: formData.faculty_id,
            name: formData.name,
            department_id: parseInt(formData.department_id),
            designation: formData.designation,
            role_category: formData.role_category,
            employment_status: formData.employment_status,
            eligibility: formData.eligibility,
            previous_js_count: Number(formData.previous_js_count),
            previous_reliever_count: Number(formData.previous_reliever_count),
            previous_standby_count: Number(formData.previous_standby_count),
            previous_ss_count: Number(formData.previous_ss_count),
          }),
        });
      }
      setModalOpen(false);
      loadData();
    } catch (err: any) {
      alert("Save failed: " + err.message);
    }
  };

  const handleExport = () => {
    window.open("/api/faculty/export/excel", "_blank");
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    try {
      const res = await fetch("/api/faculty/import/excel", {
        method: "POST",
        body,
      });
      const data = await res.json();
      alert(`Import Success: ${data.imported_count} new faculty added, ${data.updated_count} updated.`);
      loadData();
    } catch (err: any) {
      alert("Import failed: " + err.message);
    }
  };

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight">
            Faculty Master Register
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {faculty.length} Teaching faculty members across {departments.length} academic departments with historical duty indices.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium rounded cursor-pointer border border-slate-200 transition-colors">
            <Upload className="w-3.5 h-3.5 text-slate-500" />
            <span>Import Excel</span>
            <input type="file" accept=".xlsx,.xls" className="hidden" onChange={handleImportFile} />
          </label>
          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium rounded border border-slate-200 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export Excel</span>
          </button>
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Faculty</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-3 rounded-lg border border-slate-200 flex flex-col md:flex-row gap-3 items-center justify-between text-xs">
        <div className="relative w-full md:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name, ID, or designation..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded text-xs outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Department:</span>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs text-slate-800 outline-none"
            >
              <option value="all">All Departments ({departments.length})</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.code} - {d.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Role:</span>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs text-slate-800 outline-none"
            >
              <option value="all">All Roles</option>
              <option value="Faculty">Faculty (Invigilator Pool)</option>
              <option value="HOD">HOD (Senior Supervisor)</option>
              <option value="Dy. HOD">Dy. HOD (Senior Supervisor)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Faculty Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3">Faculty ID</th>
                <th className="py-2.5 px-3">Name & Official Position</th>
                <th className="py-2.5 px-3">Department</th>
                <th className="py-2.5 px-3 text-center">Category</th>
                <th className="py-2.5 px-3 text-center">Prev JS</th>
                <th className="py-2.5 px-3 text-center">Reliever</th>
                <th className="py-2.5 px-3 text-center">Standby</th>
                <th className="py-2.5 px-3 text-center">Total Duties</th>
                <th className="py-2.5 px-3 text-center">Eligibility</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    Loading faculty master register...
                  </td>
                </tr>
              ) : filteredFaculty.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    No faculty records matching the filter criteria.
                  </td>
                </tr>
              ) : (
                filteredFaculty.slice(0, 150).map((f) => (
                  <tr key={f.id} className="hover:bg-slate-50/70">
                    <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px] tabular-nums">
                      {f.faculty_id}
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="font-semibold text-slate-900">{f.name}</div>
                      <div className="text-[11px] text-slate-500">{f.designation}</div>
                    </td>
                    <td className="py-2.5 px-3 text-slate-700">{f.department_name}</td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          f.role_category === "HOD"
                            ? "bg-purple-100 text-purple-800"
                            : f.role_category === "Dy. HOD"
                            ? "bg-indigo-100 text-indigo-800"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {f.role_category}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-blue-700 tabular-nums">
                      {f.previous_js_count}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-emerald-700 tabular-nums">
                      {f.previous_reliever_count}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-amber-700 tabular-nums">
                      {f.previous_standby_count}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-slate-900 tabular-nums">
                      {f.total_previous_duties}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {f.eligibility ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-700 font-medium">
                          <CheckCircle className="w-3 h-3" /> Eligible
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] text-red-600 font-medium">
                          <XCircle className="w-3 h-3" /> Ineligible
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleOpenEdit(f)}
                          className="p-1 text-slate-400 hover:text-slate-800 rounded"
                          title="Edit"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(f.id, f.name)}
                          className="p-1 text-slate-400 hover:text-red-600 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="p-2.5 bg-slate-50 border-t border-slate-200 text-[11px] text-slate-500 flex justify-between items-center tabular-nums">
          <span>Showing {filteredFaculty.length} of {faculty.length} faculty members</span>
          <span>Centralized fairness constraints active</span>
        </div>
      </div>

      {/* Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-lg w-full p-5 border border-slate-200 text-xs">
            <h2 className="font-bold text-slate-900 text-sm mb-3">
              {editingFaculty ? "Edit Faculty Record" : "Add New Faculty Member"}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Faculty ID</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingFaculty}
                    value={formData.faculty_id}
                    onChange={(e) => setFormData({ ...formData, faculty_id: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Department</label>
                  <select
                    value={formData.department_id}
                    onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                    className="w-full p-2 bg-white border border-slate-200 rounded outline-none"
                  >
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.code} - {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full p-2 border border-slate-200 rounded outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Position / Designation</label>
                  <input
                    type="text"
                    required
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    className="w-full p-2 border border-slate-200 rounded outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Role Category</label>
                  <select
                    value={formData.role_category}
                    onChange={(e) => setFormData({ ...formData, role_category: e.target.value })}
                    className="w-full p-2 bg-white border border-slate-200 rounded outline-none"
                  >
                    <option value="Faculty">Faculty (Invigilator Pool)</option>
                    <option value="HOD">HOD (Senior Supervisor)</option>
                    <option value="Dy. HOD">Dy. HOD (Senior Supervisor)</option>
                  </select>
                </div>
              </div>

              {/* Counters */}
              <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
                <div className="text-[10px] font-bold text-slate-600 uppercase mb-2">
                  Historical Duty Baseline Counters
                </div>
                <div className="grid grid-cols-4 gap-2">
                  <div>
                    <label className="block text-[10px] text-slate-500">Prev JS</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.previous_js_count}
                      onChange={(e) => setFormData({ ...formData, previous_js_count: parseInt(e.target.value) || 0 })}
                      className="w-full p-1 border border-slate-200 rounded text-center font-bold text-blue-700"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500">Reliever</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.previous_reliever_count}
                      onChange={(e) => setFormData({ ...formData, previous_reliever_count: parseInt(e.target.value) || 0 })}
                      className="w-full p-1 border border-slate-200 rounded text-center font-bold text-emerald-700"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500">Standby</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.previous_standby_count}
                      onChange={(e) => setFormData({ ...formData, previous_standby_count: parseInt(e.target.value) || 0 })}
                      className="w-full p-1 border border-slate-200 rounded text-center font-bold text-amber-700"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500">Senior Sup.</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.previous_ss_count}
                      onChange={(e) => setFormData({ ...formData, previous_ss_count: parseInt(e.target.value) || 0 })}
                      className="w-full p-1 border border-slate-200 rounded text-center font-bold text-purple-700"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="eligibility_chk"
                  checked={formData.eligibility}
                  onChange={(e) => setFormData({ ...formData, eligibility: e.target.checked })}
                  className="rounded border-slate-300 text-blue-600"
                />
                <label htmlFor="eligibility_chk" className="text-slate-700">
                  Faculty is eligible for examination duty allocation
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                >
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
