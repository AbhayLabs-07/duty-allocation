"use client";

import React from "react";
import Link from "next/link";
import {
  CalendarDays,
  UploadCloud,
  FileCheck2,
  History,
  ArrowRight,
} from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="bg-slate-900 text-white rounded-lg p-6 sm:p-7 border border-slate-800">
        <div className="text-xs font-medium text-slate-400 mb-1">
          TCET Central Examination Section
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Welcome CoE
        </h1>
        <p className="text-slate-300 text-sm mt-1">
          Dr. Sanjeev Chaudhari, Controller of Examinations
        </p>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <Link
            href="/allocation"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded transition-colors"
          >
            <CalendarDays className="w-4 h-4" />
            <span>Create Duty Allocation</span>
            <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
          </Link>
          <Link
            href="/timetables/upload"
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded border border-slate-700 transition-colors"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Timetable</span>
          </Link>
        </div>
      </div>

      {/* Primary Shortcuts */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          href="/allocation"
          className="p-4 rounded-lg bg-white border border-slate-200 hover:border-slate-300 transition-colors block space-y-1.5"
        >
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
            <CalendarDays className="w-4 h-4 text-blue-600" />
            <span>Duty Allocation</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Upload timetable & faculty documents, select exam session, and generate duty chart.
          </p>
        </Link>

        <Link
          href="/timetables/records"
          className="p-4 rounded-lg bg-white border border-slate-200 hover:border-slate-300 transition-colors block space-y-1.5"
        >
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
            <FileCheck2 className="w-4 h-4 text-slate-700" />
            <span>Timetable Records</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Review parsed examination schedules, dates, and registered courses.
          </p>
        </Link>

        <Link
          href="/history"
          className="p-4 rounded-lg bg-white border border-slate-200 hover:border-slate-300 transition-colors block space-y-1.5"
        >
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
            <History className="w-4 h-4 text-slate-700" />
            <span>Duty History</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Access previous duty charts and export attendance registers.
          </p>
        </Link>
      </div>
    </div>
  );
}
