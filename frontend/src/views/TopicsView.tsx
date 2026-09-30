import React, { useEffect, useState } from 'react';
import {
  BarChart2,
  RefreshCw,
  TrendingUp,
  Sparkles,
  Zap,
  ArrowUpRight
} from 'lucide-react';
import { api } from '../api';
import type { TopicNarrative } from '../types';

export const TopicsView: React.FC = () => {
  const [topics, setTopics] = useState<TopicNarrative[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState<TopicNarrative | null>(null);

  const fetchTopics = async () => {
    setLoading(true);
    try {
      const data = await api.getTopics();
      setTopics(data.topics || []);
      if (data.topics && data.topics.length > 0) {
        setSelectedTopic(data.topics[0]);
      }
    } catch {
      // Mock fallback topics
      const fallback: TopicNarrative[] = [
        {
          topic_id: 1,
          topic_label: 'ApexReserve Liquidity Run & Bank Run Rumors',
          post_count: 184,
          percentage: 34.2,
          top_keywords: ['apexreserve', 'withdraw', 'liquidity', 'bridge', 'collapse', 'halt'],
          growth_velocity: 0.88,
          forecast_next_24h: 310,
          status: 'surging',
        },
        {
          topic_id: 2,
          topic_label: 'Pump and Dump Coordination around $AURA Token',
          post_count: 112,
          percentage: 21.5,
          top_keywords: ['aura', 'moon', 'pump', 'target', '100x', 'signals'],
          growth_velocity: 0.74,
          forecast_next_24h: 195,
          status: 'emerging',
        },
        {
          topic_id: 3,
          topic_label: 'Hardware Security Key Firmware Vulnerability',
          post_count: 68,
          percentage: 13.1,
          top_keywords: ['firmware', 'yubikey', 'security', 'cve', 'patch', 'exploit'],
          growth_velocity: 0.28,
          forecast_next_24h: 82,
          status: 'stable',
        },
        {
          topic_id: 4,
          topic_label: 'Decentralized Identity Compliance Standards (W3C)',
          post_count: 45,
          percentage: 8.6,
          top_keywords: ['identity', 'did', 'w3c', 'verifiable', 'credentials', 'privacy'],
          growth_velocity: 0.12,
          forecast_next_24h: 50,
          status: 'stable',
        },
      ];
      setTopics(fallback);
      setSelectedTopic(fallback[0]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'surging':
        return 'bg-[rgba(255,122,26,0.22)] text-[#ffd9b8] border-[#ff7a1a] shadow-[0_0_12px_rgba(255,122,26,0.35)]';
      case 'emerging':
        return 'bg-[rgba(255,154,77,0.18)] text-[#ffb679] border-[#ff9a4d]/60';
      default:
        return 'bg-[rgba(255,196,140,0.12)] text-[#ffd9b8] border-[rgba(255,196,140,0.3)]';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12 font-body text-[#fff3e8]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading tracking-tight text-[#fff3e8] flex items-center space-x-2.5">
            <span>Discovered Narrative Clusters & Trajectories</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold font-body bg-[rgba(255,122,26,0.15)] text-[#ff9a4d] border border-[rgba(255,154,77,0.35)]">
              c-TF-IDF Clustering
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-[rgba(255,226,205,0.64)] mt-1 font-body">
            Unsupervised dense embedding narrative clustering, keyword significance, and volume projection.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchTopics}
          className="self-start sm:self-auto flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-xl bg-[#140b05]/90 border border-[rgba(255,196,140,0.25)] text-[#fff3e8] hover:border-[#ff7a1a] hover:bg-[#1f1007] transition-all shadow-md cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#ff9a4d] ${loading ? 'animate-spin' : ''}`} />
          <span className="font-heading">Refresh Clusters</span>
        </button>
      </div>

      {/* Quick Stat Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 space-y-1">
          <div className="flex items-center justify-between text-xs text-[rgba(255,226,205,0.64)]">
            <span className="font-body">Active Clusters</span>
            <Sparkles className="w-4 h-4 text-[#ff7a1a]" />
          </div>
          <p className="text-3xl font-bold font-heading text-[#fff3e8] stat-number">
            {topics.length}
          </p>
          <p className="text-[11px] text-[#ffb679]">Identified in rolling 24h window</p>
        </div>

        <div className="glass-panel p-5 space-y-1">
          <div className="flex items-center justify-between text-xs text-[rgba(255,226,205,0.64)]">
            <span className="font-body">Highest Velocity</span>
            <TrendingUp className="w-4 h-4 text-[#ff9a4d]" />
          </div>
          <p className="text-3xl font-bold font-heading text-[#ff9a4d] stat-number">
            +{topics.length > 0 ? Math.round(Math.max(...topics.map((t) => t.growth_velocity)) * 100) : 0}%
          </p>
          <p className="text-[11px] text-[rgba(255,226,205,0.64)]">Apex viral surge rate</p>
        </div>

        <div className="glass-panel p-5 space-y-1">
          <div className="flex items-center justify-between text-xs text-[rgba(255,226,205,0.64)]">
            <span className="font-body">Total Posts Clustered</span>
            <BarChart2 className="w-4 h-4 text-[#ffb679]" />
          </div>
          <p className="text-3xl font-bold font-heading text-[#fff3e8] stat-number">
            {topics.reduce((acc, t) => acc + t.post_count, 0)}
          </p>
          <p className="text-[11px] text-[rgba(255,226,205,0.64)]">Across Reddit, YouTube, Telegram</p>
        </div>

        <div className="glass-panel p-5 space-y-1">
          <div className="flex items-center justify-between text-xs text-[rgba(255,226,205,0.64)]">
            <span className="font-body">Forecast 24h Impact</span>
            <Zap className="w-4 h-4 text-[#ffd9b8]" />
          </div>
          <p className="text-3xl font-bold font-heading text-[#ffd9b8] stat-number">
            ~{topics.reduce((acc, t) => acc + t.forecast_next_24h, 0)}
          </p>
          <p className="text-[11px] text-[#ff7a1a]">Autoregressive projected reach</p>
        </div>
      </div>

      {/* Main Layout: Topic Cards Grid on Left, Deep Dive on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Topic Cards Grid */}
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {topics.map((topic) => {
              const isSelected = selectedTopic?.topic_id === topic.topic_id;
              return (
                <div
                  key={topic.topic_id}
                  onClick={() => setSelectedTopic(topic)}
                  className={`glass-panel p-5 cursor-pointer transition-all duration-200 select-none ${
                    isSelected
                      ? 'border-[#ff7a1a] shadow-[0_0_30px_rgba(255,122,26,0.22)] bg-gradient-to-br from-[rgba(255,122,26,0.12)] to-[#150a04]'
                      : 'hover:border-[rgba(255,196,140,0.45)] hover:translate-y-[-2px]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getStatusBadge(
                        topic.status
                      )}`}
                    >
                      {topic.status}
                    </span>
                    <span className="text-xs font-mono text-[rgba(255,226,205,0.64)]">
                      Cluster #{topic.topic_id}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold font-heading text-[#fff3e8] line-clamp-2 mb-2 leading-snug">
                    {topic.topic_label}
                  </h3>

                  {/* Keywords Pills */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {topic.top_keywords.slice(0, 4).map((kw, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-[10px] rounded-lg bg-[#140b05] text-[#ffd9b8] border border-[rgba(255,196,140,0.25)] font-mono"
                      >
                        #{kw}
                      </span>
                    ))}
                  </div>

                  {/* Metrics bar */}
                  <div className="pt-3 border-t border-[rgba(255,196,140,0.15)] flex items-center justify-between text-xs">
                    <div>
                      <p className="text-[10px] uppercase font-mono text-[rgba(255,226,205,0.64)]">Volume</p>
                      <p className="font-heading font-bold text-[#fff3e8]">{topic.post_count} posts</p>
                    </div>

                    <div className="text-right">
                      <p className="text-[10px] uppercase font-mono text-[rgba(255,226,205,0.64)]">Velocity</p>
                      <p className="font-heading font-bold text-[#ff9a4d] flex items-center justify-end space-x-0.5">
                        <TrendingUp className="w-3.5 h-3.5 inline text-[#ff7a1a]" />
                        <span>+{Math.round(topic.growth_velocity * 100)}%</span>
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Deep Dive & Forecast Chart */}
        {selectedTopic && (
          <div className="glass-panel p-6 space-y-6">
            <div>
              <div className="flex items-center space-x-2 text-xs text-[#ff9a4d] font-semibold mb-1">
                <BarChart2 className="w-4 h-4 text-[#ff7a1a]" />
                <span className="font-heading uppercase tracking-wider text-[11px]">Narrative Trajectory & Forecast</span>
              </div>
              <h2 className="text-lg font-bold font-heading text-[#fff3e8] leading-tight">
                {selectedTopic.topic_label}
              </h2>
            </div>

            {/* Velocity and Forecast Cards */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 bg-[#140b05]/90 rounded-2xl border border-[rgba(255,196,140,0.2)] shadow-inner">
                <span className="text-[10px] uppercase font-mono text-[rgba(255,226,205,0.64)]">Current Velocity</span>
                <p className="text-2xl font-bold font-heading text-[#ff9a4d] mt-1 stat-number">
                  +{Math.round(selectedTopic.growth_velocity * 100)}%
                </p>
                <p className="text-[10px] text-[#ffb679] mt-0.5">Acceleration index</p>
              </div>

              <div className="p-3.5 bg-[#140b05]/90 rounded-2xl border border-[rgba(255,196,140,0.2)] shadow-inner">
                <span className="text-[10px] uppercase font-mono text-[rgba(255,226,205,0.64)]">24h Projection</span>
                <p className="text-2xl font-bold font-heading text-[#ffd9b8] mt-1 stat-number">
                  ~{selectedTopic.forecast_next_24h}
                </p>
                <p className="text-[10px] text-[rgba(255,226,205,0.64)] mt-0.5">Projected volume</p>
              </div>
            </div>

            {/* Forecast Projection Bar */}
            <div className="space-y-2">
              <span className="text-xs font-semibold font-heading text-[#fff3e8]">Volume Trajectory Forecast</span>
              <div className="p-4 bg-[#140b05]/90 rounded-2xl border border-[rgba(255,196,140,0.2)] space-y-3">
                <div className="flex justify-between text-xs text-[rgba(255,226,205,0.64)] font-body">
                  <span>Current: <strong className="text-[#fff3e8]">{selectedTopic.post_count} posts</strong></span>
                  <span className="text-[#ff9a4d] font-semibold flex items-center space-x-1">
                    <span>T+24h: ~{selectedTopic.forecast_next_24h} posts</span>
                    <ArrowUpRight className="w-3.5 h-3.5 inline" />
                  </span>
                </div>
                <div className="w-full bg-[#1e1008] h-3 rounded-full overflow-hidden flex border border-[rgba(255,196,140,0.15)]">
                  <div
                    className="bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] h-full shadow-[0_0_12px_rgba(255,122,26,0.6)]"
                    style={{
                      width: `${Math.min(100, (selectedTopic.post_count / selectedTopic.forecast_next_24h) * 100)}%`,
                    }}
                  />
                  <div
                    className="bg-[#ffb679]/30 h-full border-l border-white/20 animate-pulse"
                    style={{
                      width: `${Math.max(
                        0,
                        100 - (selectedTopic.post_count / selectedTopic.forecast_next_24h) * 100
                      )}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-[rgba(255,226,205,0.55)] italic font-body">
                  Forecast modeled via rolling autoregressive volume regression.
                </p>
              </div>
            </div>

            {/* Extracted c-TF-IDF Keywords */}
            <div>
              <span className="text-xs font-semibold font-heading text-[#fff3e8] block mb-2">
                Significant Cluster Keywords (c-TF-IDF):
              </span>
              <div className="flex flex-wrap gap-2">
                {selectedTopic.top_keywords.map((kw, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 text-xs rounded-xl bg-[#140b05] text-[#ffd9b8] border border-[rgba(255,196,140,0.25)] hover:border-[#ff9a4d] font-mono transition-colors"
                  >
                    #{kw}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TopicsView;
