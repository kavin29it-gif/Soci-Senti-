import React from 'react';
import {
  Activity,
  Bot,
  FolderLock,
  LayoutDashboard,
  Search,
  Share2,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  UserCheck,
} from 'lucide-react';

import type { UserRole } from '../types';


export type ActiveTab = 'overview' | 'explore' | 'network' | 'topics' | 'cases' | 'integrity' | 'health';

interface HeaderProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  role: UserRole;
  setRole: (role: UserRole) => void;
  onOpenCopilot: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  role,
  setRole,
  onOpenCopilot,
}) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'explore', label: 'Explore & Feed', icon: Search },
    { id: 'network', label: 'Network & CIB', icon: Share2 },
    { id: 'topics', label: 'Emerging Narratives', icon: TrendingUp },
    { id: 'cases', label: 'Case Management', icon: FolderLock },
    { id: 'integrity', label: 'Evidence & Integrity', icon: ShieldCheck },
    { id: 'health', label: 'Model Health', icon: Activity },
  ];

  return (
    <header className="border-b border-slate-800/80 bg-[#0b0f19]/90 backdrop-blur sticky top-0 z-50">
      {/* Top Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 text-white shadow-lg shadow-indigo-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  SociSenti
                </span>
                <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded-full">
                  Explainable Intelligence
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Multi-Platform Signal Fusion & Cryptographic Audit
              </p>
            </div>
          </div>

          {/* Controls: Role Switcher & Copilot Button */}
          <div className="flex items-center space-x-4">
            {/* System Status Beacon */}
            <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>4 Engines Parallel</span>
            </div>

            {/* Role Switcher */}
            <div className="flex items-center space-x-1 p-1 bg-slate-900 border border-slate-800 rounded-lg text-xs">
              <div className="px-2 py-1 text-slate-400 flex items-center space-x-1">
                <UserCheck className="w-3.5 h-3.5" />
                <span className="hidden md:inline">Role:</span>
              </div>
              {(['analyst', 'reviewer', 'admin'] as UserRole[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className={`px-2.5 py-1 rounded capitalize font-medium transition-all ${
                    role === r
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            {/* AI Copilot Button (v2 scoped) */}
            <button
              onClick={onOpenCopilot}
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-purple-900/40 via-indigo-900/40 to-slate-800 text-purple-300 border border-purple-500/30 hover:border-purple-400/60 transition-all shadow-sm group"
            >
              <Bot className="w-4 h-4 text-purple-400 group-hover:rotate-12 transition-transform" />
              <span>AI Copilot</span>
              <span className="px-1.5 py-0.2 bg-purple-500/20 text-purple-300 rounded text-[9px] uppercase tracking-wider font-bold">
                v2
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex space-x-1 overflow-x-auto py-2 border-t border-slate-800/60 scrollbar-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ActiveTab)}
                className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-inner'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
