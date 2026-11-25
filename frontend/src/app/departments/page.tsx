"use client";

import React, { useEffect, useState } from "react";
import { Building2, Plus, Edit2, Trash2, Search, Users, ShieldAlert, Mail } from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function DepartmentManagementPage() {
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState<any | null>(null);
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    hod_name: "",
    contact_email: "",
  });

  const loadDepartments = async () => {
    try {
      setLoading(true);
      const data = await fetchApi("/departments");
      setDepartments(data);
      setLoading(false);
    } catch (err: any) {
      alert("Error loading departments: " + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDepartments();
  }, []);

  const handleOpenAdd = () => {
    setEditingDept(null);
    setFormData({ code: "", name: "", hod_name: "", contact_email: "" });
    setModalOpen(true);
  };

  const handleOpenEdit = (d: any) => {
    setEditingDept(d);
    setFormData({
      code: d.code,
      name: d.name,
      hod_name: d.hod_name || "",
      contact_email: d.contact_email || "",
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Are you sure you want to delete department "${name}"? All associated faculty records will be affected.`)) return;
    try {
      await fetchApi(`/departments/${id}`, { method: "DELETE" });
      loadDepartments();
    } catch (err: any) {
      alert("Delete failed: " + err.message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingDept) {
        await fetchApi(`/departments/${editingDept.id}`, {
          method: "PUT",
          body: JSON.stringify(formData),
        });
      } else {
        await fetchApi("/departments", {
          method: "POST",
          body: JSON.stringify(formData),
        });
      }
      setModalOpen(false);
      loadDepartments();
    } catch (err: any) {
      alert("Failed to save department: " + err.message);
    }
  };

  const filtered = departments.filter((d) =>
    d.name.toLowerCase().includes(search.toLowerCase()) ||
    d.code.toLowerCase().includes(search.toLowerCase()) ||
    (d.hod_name && d.hod_name.toLowerCase().includes(search.toLowerCase()))
  );

  const totalFacultyCount = departments.reduce((acc, d) => acc + (d.faculty_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Department Governance</h1>
          <p className="text-xs text-slate-500 mt-1">
            {departments.length} Registered Academic & Administrative Departments with {totalFacultyCount} total faculty. Centralized allocation policy enforces institutional equity across all branches.
          </p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Department</span>
        </button>
      </div>

      {/* Search and Summary bar */}
      <div className="bg-white p-3.5 rounded-lg border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by code, department name, or HOD..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-slate-400 focus:bg-white"
          />
        </div>
        <div className="text-xs text-slate-500 tabular-nums">
          Showing <span className="font-semibold text-slate-900">{filtered.length}</span> of {departments.length} departments
        </div>
      </div>

      {/* High-density Institutional Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3.5 w-16 text-center">Code</th>
                <th className="py-2.5 px-3.5">Department Name</th>
                <th className="py-2.5 px-3.5">Head of Department (HOD)</th>
                <th className="py-2.5 px-3.5">Official Contact</th>
                <th className="py-2.5 px-3.5 text-right w-32">Faculty Count</th>
                <th className="py-2.5 px-3.5 text-center w-28">Policy Status</th>
                <th className="py-2.5 px-3.5 text-right w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    Loading department records...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No departments matching search criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3.5 text-center">
                      <span className="font-mono font-bold text-slate-800 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-[11px]">
                        {d.code}
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 font-semibold text-slate-900">
                      {d.name}
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-700">
                      {d.hod_name || <span className="text-slate-400 italic">Unassigned</span>}
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-500 font-mono text-[11px]">
                      {d.contact_email || <span className="text-slate-400">-</span>}
                    </td>
                    <td className="py-2.5 px-3.5 text-right font-mono font-semibold text-slate-800 tabular-nums">
                      {d.faculty_count}
                    </td>
                    <td className="py-2.5 px-3.5 text-center">
                      <span className="inline-block px-2 py-0.5 text-[10px] font-medium text-emerald-800 bg-emerald-50 border border-emerald-200 rounded">
                        Centralized
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleOpenEdit(d)}
                          className="p-1 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded"
                          title="Edit Department"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(d.id, d.name)}
                          className="p-1 text-slate-400 hover:text-red-700 hover:bg-red-50 rounded"
                          title="Delete Department"
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
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-5 border border-slate-200">
            <h3 className="text-sm font-bold text-slate-900 mb-3">
              {editingDept ? "Edit Department Details" : "Add Academic Department"}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Department Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. COMP, IT, MECH"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md outline-none uppercase font-semibold text-slate-900 focus:bg-white focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Department Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Computer Engineering"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md outline-none text-slate-900 focus:bg-white focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Head of Department (HOD)</label>
                <input
                  type="text"
                  placeholder="e.g. Dr. Rajesh K. Sharma"
                  value={formData.hod_name}
                  onChange={(e) => setFormData({ ...formData, hod_name: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md outline-none text-slate-900 focus:bg-white focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Official Contact Email</label>
                <input
                  type="email"
                  placeholder="e.g. hod.comp@tcetmumbai.in"
                  value={formData.contact_email}
                  onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md outline-none text-slate-900 focus:bg-white focus:border-slate-400"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md"
                >
                  Save Department
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
