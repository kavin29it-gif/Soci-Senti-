import React from 'react';
import {
  Bot,
  Menu,
  ShieldAlert,
  UserCheck,
  X
} from 'lucide-react';
import type { UserRole } from '../types';

interface GlobalHeaderProps {
  role: UserRole;
  setRole: (role: UserRole) => void;
  onOpenCopilot: () => void;
  isMobileSidebarOpen: boolean;
  onToggleMobileSidebar: () => void;
}

export const GlobalHeader: React.FC<GlobalHeaderProps> = ({
  role,
  setRole,
  onOpenCopilot,
  isMobileSidebarOpen,
  onToggleMobileSidebar,
}) => {
  return (
    <header className="sticky top-0 z-40 h-16 border-b border-[rgba(255,196,140,0.18)] bg-[#0b0603]/85 backdrop-blur-[22px] px-4 sm:px-6 flex items-center justify-between shadow-lg shadow-black/40">
      {/* Left: Mobile Drawer Button + SociSenti Branding */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Mobile Hamburger Drawer Toggle */}
        <button
          type="button"
          onClick={onToggleMobileSidebar}
          aria-label="Toggle Navigation Sidebar"
          className="lg:hidden p-2 rounded-xl bg-[#140b05] border border-[rgba(255,196,140,0.2)] text-[#fff3e8] hover:border-[#ff7a1a] transition-colors cursor-pointer"
        >
          {isMobileSidebarOpen ? <X className="w-5 h-5 text-[#ff9a4d]" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Brand Icon */}
        <div className="p-2 rounded-xl bg-gradient-to-tr from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] text-[#0b0603] shadow-md shadow-[#ff7a1a]/25 shrink-0">
          <ShieldAlert className="w-5 h-5" />
        </div>

        {/* Brand Titles */}
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-lg sm:text-xl font-bold font-heading tracking-tight text-[#fff3e8]">
              SociSenti
            </span>
            <span className="px-2 py-0.5 text-[9px] sm:text-[10px] font-semibold uppercase tracking-wider bg-[rgba(255,122,26,0.12)] text-[#ff9a4d] border border-[rgba(255,154,77,0.3)] rounded-full">
              Explainable Intelligence
            </span>
          </div>
          <p className="text-[11px] text-[rgba(255,226,205,0.64)] font-body hidden sm:block leading-tight">
            Multi-Platform Signal Fusion & Cryptographic Audit
          </p>
        </div>
      </div>

      {/* Right: Status Beacon + Role Switcher + AI Copilot + Profile */}
      <div className="flex items-center space-x-2 sm:space-x-3.5">
        {/* System Parallel Status Beacon */}
        <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-[rgba(255,122,26,0.1)] border border-[rgba(255,154,77,0.25)] text-[#ff9a4d] text-xs font-medium font-body">
          <span className="w-2 h-2 rounded-full bg-[#ff7a1a] animate-pulse" />
          <span>4 Engines Parallel</span>
        </div>

        {/* Role Selector: Analyst / Reviewer / Admin */}
        <div className="flex items-center space-x-1 p-0.5 sm:p-1 bg-[#140b05] border border-[rgba(255,196,140,0.2)] rounded-xl text-xs">
          <div className="px-1.5 sm:px-2 py-1 text-[rgba(255,226,205,0.64)] flex items-center space-x-1">
            <UserCheck className="w-3.5 h-3.5 text-[#ff9a4d]" />
            <span className="hidden xl:inline text-[11px]">Role:</span>
          </div>
          {(['analyst', 'reviewer', 'admin'] as UserRole[]).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`px-2.5 py-1 rounded-lg capitalize font-medium text-xs transition-all cursor-pointer ${
                role === r
                  ? 'bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603] shadow-md shadow-[#ff7a1a]/30 font-bold'
                  : 'text-[rgba(255,226,205,0.64)] hover:text-[#fff3e8] hover:bg-[#1f1007]'
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* AI Copilot Launch Button */}
        <button
          type="button"
          onClick={onOpenCopilot}
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-[rgba(255,122,26,0.18)] via-[rgba(255,154,77,0.15)] to-[#1a0e07] text-[#ffd9b8] border border-[rgba(255,154,77,0.35)] hover:border-[#ff9a4d] transition-all shadow-sm group cursor-pointer"
        >
          <Bot className="w-4 h-4 text-[#ff9a4d] group-hover:rotate-12 transition-transform" />
          <span className="hidden sm:inline font-heading">AI Copilot</span>
          <span className="px-1.5 py-0.2 bg-[#ff7a1a]/25 text-[#ffd9b8] rounded text-[9px] uppercase tracking-wider font-bold">
            v2
          </span>
        </button>

        {/* User / Profile Avatar Control */}
        <div className="flex items-center pl-1 sm:pl-2 border-l border-[rgba(255,196,140,0.18)]">
          <div
            className="w-8 h-8 rounded-full bg-gradient-to-br from-[#ff7a1a] to-[#ff9a4d] flex items-center justify-center text-[#0b0603] text-xs font-bold font-heading border border-[rgba(255,226,205,0.5)] shadow-sm"
            title={`Active User (${role})`}
          >
            {role[0].toUpperCase()}
          </div>
        </div>
      </div>
    </header>
  );
};
