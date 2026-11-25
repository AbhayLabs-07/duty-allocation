"use client";

import React, { useEffect, useState } from "react";
import { CalendarCheck, Clock, DoorOpen, Plus, Edit2, CheckCircle2 } from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function ExaminationManagementPage() {
  const [examinations, setExaminations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedShift, setSelectedShift] = useState<any | null>(null);
  const [blockCountInput, setBlockCountInput] = useState<number>(32);
  const [roomListInput, setRoomListInput] = useState<string>("");
  const [blockModalOpen, setBlockModalOpen] = useState(false);

  const loadExams = async () => {
    try {
      setLoading(true);
      const data = await fetchApi("/examinations");
      setExaminations(data);
      setLoading(false);
    } catch (err: any) {
      alert("Error loading exams: " + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExams();
  }, []);

  const handleEditBlocks = (shift: any) => {
    setSelectedShift(shift);
    setBlockCountInput(shift.block_count || 32);
    setRoomListInput(shift.room_list_str || "");
    setBlockModalOpen(true);
  };

  const handleSaveBlocks = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedShift) return;
    try {
      await fetchApi(
        `/examinations/shifts/${selectedShift.id}/blocks?block_count=${blockCountInput}&room_list_str=${encodeURIComponent(
          roomListInput
        )}`,
        { method: "PUT" }
      );
      setBlockModalOpen(false);
      loadExams();
    } catch (err: any) {
      alert("Failed to update blocks: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">Examination Sessions & Room Blocks</h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure examination sessions, shifts, classroom block capacities, and room assignments. Junior Supervisor (JS) positions are derived directly from active blocks.
        </p>
      </div>

      <div className="space-y-5">
        {loading ? (
          <div className="py-12 text-center text-slate-400">Loading examination schedules...</div>
        ) : examinations.length === 0 ? (
          <div className="py-12 text-center text-slate-400 bg-white border border-slate-200 rounded-lg">
            No examination schedules configured yet.
          </div>
        ) : (
          examinations.map((exam) => (
            <div key={exam.id} className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
              {/* Exam Header */}
              <div className="border-b border-slate-200 bg-slate-50/70 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-800">
                      {exam.exam_level}
                    </span>
                    <span className="text-xs text-slate-500 tabular-nums">AY: {exam.academic_year}</span>
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-xs text-slate-600 font-medium">{exam.semester}</span>
                  </div>
                  <h2 className="text-base font-bold text-slate-900 mt-1">{exam.name}</h2>
                </div>
                <div className="text-xs text-slate-600 sm:text-right font-mono tabular-nums">
                  <span className="text-slate-400">Schedule: </span>
                  <span className="font-semibold text-slate-800">{exam.start_date}</span> to{" "}
                  <span className="font-semibold text-slate-800">{exam.end_date}</span>
                </div>
              </div>

              {/* Dates and Shifts */}
              <div className="p-4 space-y-4">
                {exam.dates.map((d: any) => (
                  <div key={d.id} className="border border-slate-200 rounded-lg p-3.5 bg-white">
                    <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
                      <div className="flex items-center gap-2">
                        <CalendarCheck className="w-4 h-4 text-slate-600" />
                        <span className="text-xs font-bold text-slate-900 font-mono tabular-nums">
                          {d.exam_date}
                        </span>
                        <span className="text-xs text-slate-500">({d.day_name})</span>
                      </div>
                      <span className="text-[11px] font-medium text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded tabular-nums">
                        {d.shifts.length} Shift{d.shifts.length !== 1 ? "s" : ""}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {d.shifts.map((s: any) => (
                        <div
                          key={s.id}
                          className="bg-slate-50/70 p-3.5 rounded border border-slate-200 flex flex-col justify-between"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-900">{s.shift_name} Shift</span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                                s.status === "Published"
                                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                                  : s.status === "Allocated"
                                  ? "bg-blue-50 text-blue-800 border-blue-200"
                                  : "bg-slate-100 text-slate-700 border-slate-200"
                              }`}
                            >
                              {s.status}
                            </span>
                          </div>

                          <div className="mt-2.5 flex items-center justify-between text-xs text-slate-600">
                            <span className="flex items-center gap-1 font-mono text-[11px] text-slate-500 tabular-nums">
                              <Clock className="w-3.5 h-3.5 text-slate-400" />
                              {s.start_time} - {s.end_time}
                            </span>
                            <span className="font-mono font-bold text-slate-900 bg-white border border-slate-200 px-2 py-0.5 rounded text-[11px] tabular-nums">
                              {s.block_count} Blocks (JS)
                            </span>
                          </div>

                          <div className="mt-2 text-[11px] text-slate-500 font-mono truncate">
                            Rooms: {s.room_list_str || "Unspecified"}
                          </div>

                          <div className="mt-3 pt-2 border-t border-slate-200/80 flex items-center justify-end">
                            <button
                              onClick={() => handleEditBlocks(s)}
                              className="text-xs font-semibold text-slate-700 hover:text-slate-900 flex items-center gap-1 transition-colors"
                            >
                              <Edit2 className="w-3 h-3 text-slate-500" />
                              <span>Configure Blocks / Rooms</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Block Edit Modal */}
      {blockModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-5 border border-slate-200">
            <h3 className="text-sm font-bold text-slate-900 mb-2">
              Configure Classroom Blocks & Room Numbers
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Shift: <span className="font-semibold text-slate-800">{selectedShift?.shift_name}</span>. The number of blocks defines the exact Junior Supervisor (JS) requirement.
            </p>

            <form onSubmit={handleSaveBlocks} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Active Examination Blocks (JS Count)
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  value={blockCountInput}
                  onChange={(e) => setBlockCountInput(parseInt(e.target.value) || 1)}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md font-mono font-bold text-slate-900 outline-none focus:bg-white focus:border-slate-400 tabular-nums"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Room Numbers / Blocks (Comma-separated)
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. 101, 102, 103, 104, 201, 202, 203..."
                  value={roomListInput}
                  onChange={(e) => setRoomListInput(e.target.value)}
                  className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-md font-mono text-slate-800 outline-none focus:bg-white focus:border-slate-400"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setBlockModalOpen(false)}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md"
                >
                  Save Configuration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
