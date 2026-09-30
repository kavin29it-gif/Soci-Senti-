import React, { useState, type ReactNode } from 'react';
import { GlobalHeader } from './GlobalHeader';
import { SidebarNavigation, type NavTabId } from './SidebarNavigation';
import { GlassGlobe } from './GlassGlobe';
import type { UserRole } from '../types';
import { Shield, Lock } from 'lucide-react';

interface AppShellProps {
  children: ReactNode;
  activeTab: NavTabId;
  setActiveTab: (tab: NavTabId) => void;
  role: UserRole;
  setRole: (role: UserRole) => void;
  onOpenCopilot: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeTab,
  setActiveTab,
  role,
  setRole,
  onOpenCopilot,
}) => {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0b0603] text-[#fff3e8] flex flex-col font-body relative overflow-x-hidden selection:bg-[#ff7a1a]/30 selection:text-[#ffd9b8]">
      {/* 3D Rotating Dot Globe Background Canvas (z-0, fixed, drag-to-rotate) */}
      <GlassGlobe />

      {/* 1. Global Fixed Top Header */}
      <GlobalHeader
        role={role}
        setRole={setRole}
        onOpenCopilot={onOpenCopilot}
        isMobileSidebarOpen={isMobileSidebarOpen}
        onToggleMobileSidebar={() => setIsMobileSidebarOpen((prev) => !prev)}
      />

      {/* 2. Middle Row: Glass Sidebar + Main Content (relative z-10) */}
      <div className="flex flex-1 relative z-10">
        <SidebarNavigation
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onOpenCopilot={onOpenCopilot}
          isOpenMobile={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
        />

        <main className="flex-1 w-full min-w-0 px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto overflow-x-hidden">
          {children}
        </main>
      </div>

      {/* 3. Warm Glass Footer */}
      <footer className="border-t border-[rgba(255,196,140,0.18)] bg-[#0b0603]/85 backdrop-blur-[22px] py-5 text-xs text-[rgba(255,226,205,0.64)] mt-auto relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 font-body">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-[#ff7a1a]" />
            <span className="text-[#fff3e8] font-semibold font-heading">SociSenti Platform (MVP v1.0)</span>
            <span className="text-[rgba(255,196,140,0.3)]">|</span>
            <span>Zero-Trust Explainable Social Intelligence</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1.5 text-[#ff9a4d]">
              <Lock className="w-3.5 h-3.5 text-[#ff7a1a]" />
              <span>Salted SHA-256 Author Privacy Enforced</span>
            </span>
            <span className="text-[rgba(255,196,140,0.3)]">|</span>
            <span>pgvector HNSW Embedded</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AppShell;
