import React from 'react';
import {
  Activity,
  Bot,
  FolderLock,
  LayoutDashboard,
  Lock,
  Search,
  Share2,
  Shield,
  ShieldCheck,
  TrendingUp,
  X
} from 'lucide-react';
import type { ActiveTab } from './Header';

export type NavTabId = ActiveTab | 'copilot';

interface SidebarNavigationProps {
  activeTab: NavTabId;
  setActiveTab: (tab: NavTabId) => void;
  onOpenCopilot: () => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  id: NavTabId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeColor?: string;
  isAction?: boolean;
}

export const SidebarNavigation: React.FC<SidebarNavigationProps> = ({
  activeTab,
  setActiveTab,
  onOpenCopilot,
  isOpenMobile,
  onCloseMobile,
}) => {
  const navSections: { title: string; items: NavItem[] }[] = [
    {
      title: 'INTELLIGENCE MONITORING',
      items: [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'explore', label: 'Explore & Feed', icon: Search },
        { id: 'network', label: 'Network & CIB', icon: Share2 },
        { id: 'topics', label: 'Emerging Narratives', icon: TrendingUp },
      ],
    },
    {
      title: 'COMPLIANCE & INTEGRITY',
      items: [
        { id: 'cases', label: 'Case Management', icon: FolderLock },
        { id: 'integrity', label: 'Evidence & Integrity', icon: ShieldCheck },
        { id: 'health', label: 'Model Health', icon: Activity },
      ],
    },
    {
      title: 'ASSISTANCE',
      items: [
        {
          id: 'copilot',
          label: 'AI Copilot',
          icon: Bot,
          badge: 'v2',
          badgeColor: 'bg-[rgba(255,122,26,0.18)] text-[#ffd9b8] border-[rgba(255,154,77,0.3)]',
          isAction: true,
        },
      ],
    },
  ];

  const handleItemClick = (item: NavItem) => {
    if (item.isAction && item.id === 'copilot') {
      onOpenCopilot();
      onCloseMobile();
      return;
    }
    setActiveTab(item.id);
    onCloseMobile();
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#0b0603]/80 backdrop-blur-[22px] border-r border-[rgba(255,196,140,0.18)] w-64 select-none">
      {/* Mobile Drawer Header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b border-[rgba(255,196,140,0.18)]">
        <div className="flex items-center space-x-2">
          <Shield className="w-5 h-5 text-[#ff7a1a]" />
          <span className="font-heading font-bold text-[#fff3e8] tracking-wide">SociSenti Navigation</span>
        </div>
        <button
          type="button"
          onClick={onCloseMobile}
          className="p-1.5 rounded-xl bg-[#140b05] border border-[rgba(255,196,140,0.2)] text-[rgba(255,226,205,0.64)] hover:text-[#fff3e8] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-5 space-y-6 scrollbar-thin scrollbar-thumb-[rgba(255,122,26,0.25)]">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1.5">
            <h2 className="px-3 text-[10px] font-bold tracking-wider uppercase text-[rgba(255,196,140,0.55)] font-mono">
              {section.title}
            </h2>
            <div className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleItemClick(item)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium font-body transition-all group cursor-pointer ${
                      isActive
                        ? 'bg-gradient-to-r from-[rgba(255,122,26,0.2)] via-[rgba(255,154,77,0.12)] to-transparent text-[#fff3e8] font-bold border-l-[3px] border-[#ff7a1a] shadow-[inset_0_1px_0_rgba(255,226,205,0.15)] shadow-[#ff7a1a]/15'
                        : 'text-[rgba(255,226,205,0.64)] hover:text-[#fff3e8] hover:bg-[#1a0f08]/70 border-l-[3px] border-transparent'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Icon
                        className={`w-4 h-4 transition-colors ${
                          isActive
                            ? 'text-[#ff9a4d] drop-shadow-[0_0_8px_rgba(255,122,26,0.6)]'
                            : 'text-[rgba(255,196,140,0.45)] group-hover:text-[#ffd9b8]'
                        }`}
                      />
                      <span className="tracking-tight">{item.label}</span>
                    </div>

                    {item.badge && (
                      <span
                        className={`px-1.5 py-0.2 rounded text-[9px] font-bold uppercase tracking-wider border ${
                          item.badgeColor || 'bg-[#1a0f08] text-[#ffd9b8] border-[rgba(255,196,140,0.25)]'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Sidebar Footer Card */}
      <div className="p-3 border-t border-[rgba(255,196,140,0.18)] bg-[#0b0603]/90 space-y-2">
        <div className="p-3 rounded-2xl bg-[#140b05]/90 border border-[rgba(255,196,140,0.2)] text-[11px] space-y-1.5 shadow-md">
          <div className="flex items-center justify-between text-[#fff3e8] font-semibold">
            <span className="flex items-center space-x-1.5 text-[#ff9a4d]">
              <Lock className="w-3.5 h-3.5 text-[#ff7a1a]" />
              <span>Zero-Trust Enforced</span>
            </span>
            <span className="text-[10px] text-[rgba(255,196,140,0.6)] font-mono">v1.0.0</span>
          </div>
          <p className="text-[10px] text-[rgba(255,226,205,0.64)] font-body leading-tight">
            Author privacy protected via Salted SHA-256. pgvector HNSW active.
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Left Sidebar */}
      <aside className="hidden lg:block shrink-0 h-[calc(100vh-4rem)] sticky top-16 z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isOpenMobile && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity animate-fade-in"
            onClick={onCloseMobile}
          />
          {/* Drawer Panel */}
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-[#0b0603] z-10 shadow-2xl animate-slide-right">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
