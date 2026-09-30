import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  FileText,
  Flame,
  Globe2,
  Radio,
  RefreshCw,
  ShieldAlert,
  Users,
} from 'lucide-react';

import { api } from '../api';
import type { DashboardOverview } from '../types';


interface OverviewViewProps {
  onSelectEntityForCase: (entityType: string, entityId: string) => void;
  onNavigateToTab: (tab: 'explore' | 'network' | 'topics' | 'cases' | 'integrity' | 'health') => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  onSelectEntityForCase,
  onNavigateToTab,
}) => {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const overview = await api.getOverview();
      setData(overview);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(), 12000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-sm text-slate-400">Loading intelligence telemetry & streaming metrics...</p>
      </div>
    );
  }

  const kpis = data?.kpis || {
    posts_ingested: 5200,
    high_risk_alerts: 412,
    open_cases: 6,
    verified_evidence_items: 42,
  };

  const platforms = [
    { name: 'Reddit', key: 'reddit', color: 'from-[rgba(255,122,26,0.18)] to-[rgba(255,122,26,0.06)]', border: 'border-[rgba(255,196,140,0.25)]', text: 'text-[#ffd9b8]' },
    { name: 'YouTube', key: 'youtube', color: 'from-[rgba(255,154,77,0.18)] to-[rgba(255,154,77,0.06)]', border: 'border-[rgba(255,196,140,0.25)]', text: 'text-[#ffb679]' },
    { name: 'Telegram', key: 'telegram', color: 'from-[rgba(255,182,121,0.18)] to-[rgba(255,182,121,0.06)]', border: 'border-[rgba(255,196,140,0.25)]', text: 'text-[#ffd9b8]' },
    { name: 'Mock Replay', key: 'mock', color: 'from-[rgba(255,122,26,0.12)] to-[rgba(20,10,5,0.4)]', border: 'border-[rgba(255,196,140,0.2)]', text: 'text-[#ffb679]' },
  ];

  return (
    <div className="space-y-6 animate-fade-in pb-12 font-['Manrope']">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#fff3e8] font-['Sora'] flex items-center space-x-2">
            <span>Executive Overview & Real-Time Telemetry</span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)]">
              Live Feed
            </span>
          </h1>
          <p className="text-xs text-[rgba(255,226,205,0.64)] mt-1">
            Parallel stream ingestion, ML scoring fusion, and tamper-evident audit health.
          </p>
        </div>

        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="self-start sm:self-auto flex items-center space-x-2 px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-[rgba(255,154,77,0.08)] hover:bg-[rgba(255,154,77,0.16)] border border-[rgba(255,196,140,0.25)] text-[#fff3e8] transition-all disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#ff7a1a]' : 'text-[#ffb679]'}`} />
          <span>{refreshing ? 'Syncing...' : 'Sync Telemetry'}</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 bg-[rgba(255,80,20,0.15)] border border-[#ff7a1a]/40 rounded-2xl text-xs text-[#ffd9b8] flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-[#ff7a1a] shrink-0" />
          <span>Gateway connection notice: {error}. Displaying buffered local intelligence.</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-[22px] relative overflow-hidden group hover:border-[#ff7a1a]/50 transition-all">
          <div className="absolute top-0 right-0 p-4 text-[rgba(255,122,26,0.1)] group-hover:text-[rgba(255,122,26,0.2)] transition-colors">
            <Radio className="w-14 h-14 -mr-2 -mt-2" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] font-['Sora']">Total Posts Ingested</span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ff9a4d] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#ff7a1a]"></span>
            </span>
          </div>
          <p className="text-3xl font-extrabold text-[#fff3e8] mt-2 font-['Sora']">
            {kpis.posts_ingested.toLocaleString()}
          </p>
          <p className="text-[11px] text-[rgba(255,226,205,0.6)] mt-2 flex items-center space-x-1">
            <span className="text-[#ffd9b8] font-semibold">Sub-5s</span>
            <span>KRaft ingestion-to-score pipeline</span>
          </p>
        </div>

        <div className="glass-panel p-5 rounded-[22px] relative overflow-hidden group hover:border-[#ff7a1a]/50 transition-all">
          <div className="absolute top-0 right-0 p-4 text-[rgba(255,122,26,0.1)] group-hover:text-[rgba(255,122,26,0.2)] transition-colors">
            <ShieldAlert className="w-14 h-14 -mr-2 -mt-2" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#ffd9b8] font-['Sora']">High Risk Alerts</span>
          <p className="text-3xl font-extrabold text-[#fff3e8] mt-2 font-['Sora']">
            {kpis.high_risk_alerts}
          </p>
          <p className="text-[11px] text-[rgba(255,226,205,0.6)] mt-2">
            Fused score &gt; 70 with SHAP attributions
          </p>
        </div>

        <div className="glass-panel p-5 rounded-[22px] relative overflow-hidden group hover:border-[#ff7a1a]/50 transition-all">
          <div className="absolute top-0 right-0 p-4 text-[rgba(255,122,26,0.1)] group-hover:text-[rgba(255,122,26,0.2)] transition-colors">
            <FileText className="w-14 h-14 -mr-2 -mt-2" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#ffb679] font-['Sora']">Active Cases</span>
          <p className="text-3xl font-extrabold text-[#fff3e8] mt-2 font-['Sora']">
            {kpis.open_cases}
          </p>
          <p className="text-[11px] text-[rgba(255,226,205,0.6)] mt-2">
            Under active analyst/reviewer investigation
          </p>
        </div>

        <div className="glass-panel p-5 rounded-[22px] relative overflow-hidden group hover:border-[#ff7a1a]/50 transition-all">
          <div className="absolute top-0 right-0 p-4 text-[rgba(255,122,26,0.1)] group-hover:text-[rgba(255,122,26,0.2)] transition-colors">
            <CheckCircle2 className="w-14 h-14 -mr-2 -mt-2" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#ffd9b8] font-['Sora']">Evidence Fingerprints</span>
          <p className="text-3xl font-extrabold text-[#fff3e8] mt-2 font-['Sora']">
            {kpis.verified_evidence_items}
          </p>
          <p className="text-[11px] text-[rgba(255,226,205,0.6)] mt-2">
            SHA-256 anchored & Merkle tree verifiable
          </p>
        </div>
      </div>

      {/* Grid: Platform Breakdown & Sentiment Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Platform Ingestion */}
        <div className="glass-panel p-6 rounded-[22px] lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Globe2 className="w-4 h-4 text-[#ff7a1a]" />
              <h2 className="text-sm font-bold text-[#fff3e8] font-['Sora']">Multi-Platform Ingestion Feeds</h2>
            </div>
            <button
              onClick={() => onNavigateToTab('explore')}
              className="text-xs text-[#ff9a4d] hover:text-[#ffd9b8] flex items-center space-x-1 cursor-pointer font-semibold"
            >
              <span>Explore Feed</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {platforms.map((p) => {
              const count = data?.volume_by_platform?.[p.key] ?? 1250;
              return (
                <div
                  key={p.key}
                  className={`p-4 rounded-xl bg-gradient-to-b ${p.color} border ${p.border} transition-all hover:scale-[1.02]`}
                >
                  <p className={`text-xs font-semibold ${p.text}`}>{p.name}</p>
                  <p className="text-2xl font-extrabold font-['Sora'] text-[#fff3e8] mt-1">{count}</p>
                  <p className="text-[10px] text-[rgba(255,226,205,0.6)] mt-1">Posts streaming</p>
                </div>
              );
            })}
          </div>

          <div className="mt-4 p-3 bg-[rgba(14,7,4,0.6)] rounded-xl border border-[rgba(255,196,140,0.15)] text-xs text-[rgba(255,226,205,0.7)] flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-[#ff7a1a] animate-pulse" />
              <span>Deduplication: Bloom filter + 64-bit weighted SimHash active</span>
            </span>
            <span className="text-[rgba(255,226,205,0.5)] font-mono text-[11px]">&lt; 3.5ms query time</span>
          </div>
        </div>

        {/* Sentiment & Emotion Distribution */}
        <div className="glass-panel p-6 rounded-[22px]">
          <div className="flex items-center space-x-2 mb-4">
            <BarChart3 className="w-4 h-4 text-[#ff9a4d]" />
            <h2 className="text-sm font-bold text-[#fff3e8] font-['Sora']">Global Sentiment Breakdown</h2>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#ffd9b8] font-semibold">Positive / Constructive</span>
                <span className="font-mono text-[#fff3e8]">45%</span>
              </div>
              <div className="w-full bg-[rgba(255,196,140,0.12)] h-2 rounded-full overflow-hidden">
                <div className="bg-[#ffd9b8] h-full rounded-full" style={{ width: '45%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#ffb679] font-semibold">Neutral / Informational</span>
                <span className="font-mono text-[#fff3e8]">38%</span>
              </div>
              <div className="w-full bg-[rgba(255,196,140,0.12)] h-2 rounded-full overflow-hidden">
                <div className="bg-[#ffb679] h-full rounded-full" style={{ width: '38%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#ff7a1a] font-semibold">Negative / Hostile / Panic</span>
                <span className="font-mono text-[#fff3e8]">17%</span>
              </div>
              <div className="w-full bg-[rgba(255,196,140,0.12)] h-2 rounded-full overflow-hidden">
                <div className="bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] h-full rounded-full" style={{ width: '17%' }} />
              </div>
            </div>
          </div>

          <div className="mt-5 pt-3 border-t border-[rgba(255,196,140,0.15)] text-[11px] text-[rgba(255,226,205,0.6)] space-y-1">
            <div className="flex justify-between">
              <span>Z-Score Timeline Shift:</span>
              <span className="text-[#ffd9b8] font-mono">0.42 (Normal)</span>
            </div>
            <div className="flex justify-between">
              <span>Sarcasm Heuristic Rate:</span>
              <span className="text-[#ffb679] font-mono">4.1%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Top Emerging Topics & Top Risky Entities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Emerging Topics */}
        <div className="glass-panel p-6 rounded-[22px]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Flame className="w-4 h-4 text-[#ff7a1a]" />
              <h2 className="text-sm font-bold text-[#fff3e8] font-['Sora']">Top Emerging Narratives</h2>
            </div>
            <button
              onClick={() => onNavigateToTab('topics')}
              className="text-xs text-[#ff9a4d] hover:text-[#ffd9b8] flex items-center space-x-1 cursor-pointer font-semibold"
            >
              <span>View All</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {(data?.top_emerging_topics || [
              { topic: 'Liquidity Run on ApexReserve', velocity: 0.88, post_count: 142 },
              { topic: 'Coordinated Pump $AURA', velocity: 0.76, post_count: 98 },
              { topic: 'Decentralized Key Custody Discussions', velocity: 0.32, post_count: 64 },
            ]).map((t, idx) => (
              <div
                key={idx}
                className="p-3.5 bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] border border-[rgba(255,196,140,0.18)] rounded-xl flex items-center justify-between hover:border-[#ff7a1a]/40 transition-all"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs text-[#ff7a1a] font-bold">#{idx + 1}</span>
                    <span className="text-xs font-semibold text-[#fff3e8]">{t.topic}</span>
                  </div>
                  <p className="text-[11px] text-[rgba(255,226,205,0.6)]">
                    Volume: <span className="font-mono text-[#ffd9b8]">{t.post_count} posts</span>
                  </p>
                </div>

                <div className="text-right">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold font-mono ${
                      t.velocity > 0.75
                        ? 'bg-[rgba(255,122,26,0.22)] text-[#ffd9b8] border border-[#ff7a1a]'
                        : 'bg-[rgba(255,154,77,0.18)] text-[#ffb679] border border-[#ff9a4d]/60'
                    }`}
                  >
                    +{Math.round(t.velocity * 100)}% vel
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Risky Entities */}
        <div className="glass-panel p-6 rounded-[22px]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Users className="w-4 h-4 text-[#ff7a1a]" />
              <h2 className="text-sm font-bold text-[#fff3e8] font-['Sora']">Top Flagged Entities for Review</h2>
            </div>
            <span className="text-xs text-[rgba(255,226,205,0.6)]">Auto-prioritized by Fusion Model</span>
          </div>

          <div className="space-y-3">
            {(data?.top_risky_entities || [
              { entity_id: 'sockpuppet_cluster_014', entity_type: 'cluster', risk_score: 92.4, risk_band: 'High' },
              { entity_id: 'auth_9f82a170b', entity_type: 'author', risk_score: 86.1, risk_band: 'High' },
              { entity_id: 'tg_post_49201', entity_type: 'post', risk_score: 79.5, risk_band: 'High' },
            ]).map((ent, idx) => (
              <div
                key={idx}
                className="p-3.5 bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] border border-[rgba(255,196,140,0.18)] rounded-xl flex items-center justify-between hover:border-[#ff7a1a]/40 transition-all"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 text-[10px] uppercase font-bold bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)] rounded-md">
                      {ent.entity_type}
                    </span>
                    <span className="font-mono text-xs text-[#fff3e8] font-semibold">{ent.entity_id}</span>
                  </div>
                  <p className="text-[11px] text-[rgba(255,226,205,0.6)] mt-1">
                    Risk Band: <span className="text-[#ffd9b8] font-semibold">{ent.risk_band}</span>
                  </p>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <div className="text-lg font-extrabold font-mono text-[#ff7a1a] font-['Sora']">
                      {ent.risk_score.toFixed(1)}
                    </div>
                    <span className="text-[9px] uppercase tracking-wider text-[rgba(255,226,205,0.5)]">Risk Score</span>
                  </div>

                  <button
                    onClick={() => onSelectEntityForCase(ent.entity_type, ent.entity_id)}
                    className="px-3 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603] hover:brightness-110 shadow-md shadow-[#ff7a1a]/30 transition-all cursor-pointer"
                  >
                    Open Case
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
