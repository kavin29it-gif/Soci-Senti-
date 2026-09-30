import React, { useState } from 'react';
import { AppShell } from './components/AppShell';
import type { NavTabId } from './components/SidebarNavigation';
import { CopilotModal } from './components/CopilotModal';
import { OverviewView } from './views/OverviewView';
import { ExploreView } from './views/ExploreView';
import { NetworkView } from './views/NetworkView';
import { TopicsView } from './views/TopicsView';
import { CasesView } from './views/CasesView';
import { IntegrityView } from './views/IntegrityView';
import { ModelHealthView } from './views/ModelHealthView';
import type { UserRole, Post } from './types';
import { ErrorBoundary } from './components/ErrorBoundary';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTabId>('overview');
  const [role, setRole] = useState<UserRole>('analyst');
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [prefillEntity, setPrefillEntity] = useState<{ entityType: string; entityId: string } | null>(null);

  const handleSelectEntityForCase = (entityType: string, entityId: string) => {
    setPrefillEntity({ entityType, entityId });
    setActiveTab('cases');
  };

  const handleOpenCaseForPost = (post: Post) => {
    setPrefillEntity({ entityType: 'post', entityId: post.post_id });
    setActiveTab('cases');
  };

  return (
    <>
      <AppShell
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        role={role}
        setRole={setRole}
        onOpenCopilot={() => setCopilotOpen(true)}
      >
        <ErrorBoundary fallbackTitle="View Rendering Error">
          {activeTab === 'overview' && (
            <OverviewView
              onSelectEntityForCase={handleSelectEntityForCase}
              onNavigateToTab={(t) => setActiveTab(t as NavTabId)}
            />
          )}
          {activeTab === 'explore' && (
            <ExploreView onOpenCaseForPost={handleOpenCaseForPost} />
          )}
          {activeTab === 'network' && <NetworkView />}
          {activeTab === 'topics' && <TopicsView />}
          {activeTab === 'cases' && (
            <CasesView
              role={role}
              prefillEntity={prefillEntity}
              onClearPrefill={() => setPrefillEntity(null)}
            />
          )}
          {activeTab === 'integrity' && <IntegrityView />}
          {activeTab === 'health' && <ModelHealthView />}
        </ErrorBoundary>
      </AppShell>

      {/* AI Copilot Modal (v2 scoped) */}
      <CopilotModal isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </>
  );
};

export default App;
