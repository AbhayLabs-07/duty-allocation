"use client";

import React from "react";
import { Menu } from "lucide-react";

interface TopbarProps {
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export default function Topbar({ onToggleSidebar }: TopbarProps) {
  return (
    <header className="h-14 bg-white border-b border-slate-200 fixed top-0 right-0 left-0 lg:left-64 z-20 flex items-center justify-between px-4 sm:px-6 transition-all duration-200">
      {/* College & Department Context */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-1.5 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 lg:hidden"
            title="Toggle Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div className="flex items-center gap-2 text-xs">
          <span className="font-bold text-slate-900 tracking-tight">
            Thakur College of Engineering & Technology
          </span>
          <span className="text-slate-300 hidden sm:inline">/</span>
          <span className="text-slate-700 font-medium hidden sm:inline">Central Examination Section</span>
          <span className="text-slate-300 hidden md:inline">/</span>
          <span className="text-slate-500 font-mono text-[11px] hidden md:inline">AY 2025–26</span>
        </div>
      </div>

      {/* Controller of Examination Profile (No Role Switcher) */}
      <div className="flex items-center gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center border border-slate-700 shadow-sm">
            SC
          </div>
          <div className="text-left">
            <div className="text-xs font-bold text-slate-900 leading-tight">
              Dr. Sanjeev Chaudhari
            </div>
            <div className="text-[11px] font-medium text-blue-700">
              Controller of Examinations
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
