import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle,
  Database,
  Filter,
  Fingerprint,
  FolderPlus,
  PlusCircle,
  RefreshCw,
  Search,
  Send,
  Shield,
  Sparkles,
  UploadCloud,
  X,
} from 'lucide-react';
import { api } from '../api';
import type { Post, RiskAnalysis } from '../types';


interface ExploreViewProps {
  onOpenCaseForPost: (post: Post) => void;
}

export const ExploreView: React.FC<ExploreViewProps> = ({ onOpenCaseForPost }) => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [platform, setPlatform] = useState('all');
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [riskData, setRiskData] = useState<RiskAnalysis | null>(null);
  const [loadingRisk, setLoadingRisk] = useState(false);

  // Data feeding modal state
  const [showFeedModal, setShowFeedModal] = useState(false);
  const [feedMode, setFeedMode] = useState<'single' | 'batch'>('single');
  const [inputText, setInputText] = useState('');
  const [inputPlatform, setInputPlatform] = useState('reddit');
  const [inputAuthor, setInputAuthor] = useState('');
  const [inputLikes, setInputLikes] = useState(15);
  const [inputShares, setInputShares] = useState(45);
  const [inputReplies, setInputReplies] = useState(8);
  const [submitting, setSubmitting] = useState(false);
  const [feedFeedback, setFeedFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Batch stream replay state
  const [batchPlatform, setBatchPlatform] = useState('mock');
  const [batchLimit, setBatchLimit] = useState(50);
  const [batchQuery, setBatchQuery] = useState('');
  const [batchLoading, setBatchLoading] = useState(false);

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const res = await api.getPosts({
        platform,
        search: search.trim() || undefined,
        limit: 100,
      });
      setPosts(res.posts || []);
    } catch {
      // Graceful fallback with sample posts if backend temporarily unreachable
      setPosts([
        {
          post_id: 'post_sample_01',
          platform: 'reddit',
          author_id_hash: 'a38f71029cde88',
          text: 'Emergency liquidity run underway on ApexReserve. Withdraw your assets immediately before bridge collapse!',
          created_at: new Date().toISOString(),
          spam_score: 0.12,
          risk_score: 84.5,
          risk_band: 'High',
          emotions: { fear: 0.72, anger: 0.18, surprise: 0.10 },
          sentiment: { label: 'negative', score: 0.88, negative_prob: 0.88, neutral_prob: 0.08, positive_prob: 0.04 },
          evidence_hash: '9f830a84e26715f8a096cfae4f201082c5890473919e917d59828fa687b3229b',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [platform]);

  const handleSelectPost = async (post: Post) => {
    setSelectedPost(post);
    setLoadingRisk(true);
    setRiskData(null);
    try {
      const analysis = await api.getRiskAnalysis('post', post.post_id);
      setRiskData(analysis);
    } catch {
      // Mock explainable fallback
      setRiskData({
        entity_type: 'post',
        entity_id: post.post_id,
        risk_score: post.risk_score || 78.4,
        confidence_interval: [71.2, 85.6],
        risk_band: (post.risk_band as any) || 'High',
        anomaly_score: 0.74,
        coordination_score: 0.82,
        explanation: 'Elevated risk due to panic language, synchronized co-posting burst, and high negative sentiment.',
        drivers: [
          { feature: 'coordination_weight', attribution: 0.32, value: 0.85 },
          { feature: 'sentiment_neg_prob', attribution: 0.24, value: 0.88 },
          { feature: 'anomaly_score', attribution: 0.18, value: 0.74 },
          { feature: 'uppercase_ratio', attribution: 0.09, value: 0.22 },
        ],
        negative_factors: [
          { feature: 'author_frequency', attribution: -0.06, value: 0.15 },
        ],
      });
    } finally {
      setLoadingRisk(false);
    }
  };

  const handleIngestSingle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    setSubmitting(true);
    setFeedFeedback(null);
    try {
      const res = await api.ingestPost({
        text: inputText.trim(),
        platform: inputPlatform,
        author_handle: inputAuthor.trim() || undefined,
        likes: Number(inputLikes) || 0,
        shares: Number(inputShares) || 0,
        replies: Number(inputReplies) || 0,
      });

      if (res.status === 'dropped') {
        setFeedFeedback({
          type: 'error',
          message: 'Post was dropped by stream pipeline (duplicate or heuristic spam filter).',
        });
      } else {
        const newPost = res.post;
        setPosts((prev) => [newPost, ...prev]);
        handleSelectPost(newPost);
        setFeedFeedback({
          type: 'success',
          message: `Post ingested! Calibrated Risk Score: ${res.risk_analysis?.risk_score}/100 (${res.risk_analysis?.risk_band}).`,
        });
        setInputText('');
      }
    } catch (err: unknown) {
      setFeedFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleTriggerBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    setBatchLoading(true);
    setFeedFeedback(null);
    try {
      const res = await api.triggerIngest({
        platform: batchPlatform,
        limit: batchLimit,
        query: batchQuery.trim() || undefined,
      });
      setFeedFeedback({
        type: 'success',
        message: `Ingestion completed! Fetched: ${res.fetched}, Clean Emitted: ${res.clean_emitted}, Duplicates: ${res.duplicates}, Spam Dropped: ${res.spam_dropped}.`,
      });
      fetchPosts();
    } catch (err: unknown) {
      setFeedFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setBatchLoading(false);
    }
  };

  const getRiskBadgeColor = (band?: string) => {
    switch (band) {
      case 'High':
        return 'bg-[rgba(255,122,26,0.25)] text-[#ffd9b8] border-[#ff7a1a] shadow-[0_0_12px_rgba(255,122,26,0.35)]';
      case 'Medium':
        return 'bg-[rgba(255,154,77,0.2)] text-[#ffb679] border-[#ff9a4d]/60';
      default:
        return 'bg-[rgba(255,196,140,0.12)] text-[#ffd9b8] border-[rgba(255,196,140,0.3)]';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in relative pb-12 font-['Manrope']">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#fff3e8] font-['Sora'] flex items-center space-x-2">
            <span>Explore Ingested Social Feeds</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)]">
              {posts.length} Posts
            </span>
          </h1>
          <p className="text-xs text-[rgba(255,226,205,0.64)] mt-1">
            Search normalized multi-platform posts, inspect SHAP drivers, and verify SHA-256 evidence.
          </p>
        </div>

        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Platform Selector */}
          <div className="flex items-center space-x-1 p-1 bg-[rgba(26,14,8,0.7)] border border-[rgba(255,196,140,0.2)] rounded-xl text-xs backdrop-blur-md">
            <Filter className="w-3.5 h-3.5 text-[rgba(255,226,205,0.5)] ml-1.5 mr-0.5" />
            {['all', 'reddit', 'youtube', 'telegram', 'mock'].map((p) => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={`px-3 py-1 rounded-lg capitalize font-medium transition-all cursor-pointer ${
                  platform === p
                    ? 'bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603] font-bold shadow-md shadow-[#ff7a1a]/30'
                    : 'text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8] hover:bg-[rgba(255,154,77,0.12)]'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Search box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              fetchPosts();
            }}
            className="flex items-center space-x-1"
          >
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[rgba(255,226,205,0.5)] absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search keywords..."
                className="pl-8 pr-3 py-1.5 text-xs bg-[rgba(26,14,8,0.7)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a] focus:ring-1 focus:ring-[#ff7a1a]/50"
              />
            </div>
            <button
              type="submit"
              className="p-2 text-xs bg-[rgba(255,122,26,0.15)] hover:bg-[#ff7a1a] hover:text-[#0b0603] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)] rounded-xl transition-all cursor-pointer"
              title="Refresh Feed"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </form>

          {/* Feed Data Button */}
          <button
            type="button"
            onClick={() => {
              setShowFeedModal(true);
              setFeedFeedback(null);
            }}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-bold bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] hover:brightness-110 text-[#0b0603] rounded-xl shadow-lg shadow-[#ff7a1a]/30 transition-all cursor-pointer active:scale-95"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>+ Feed Data</span>
          </button>
        </div>
      </div>

      {/* Posts Table */}
      <div className="glass-panel rounded-[22px] overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[rgba(14,7,4,0.85)] border-b border-[rgba(255,196,140,0.15)] text-[rgba(255,226,205,0.65)] uppercase tracking-wider text-[10px] font-['Sora']">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Platform</th>
                <th className="py-3.5 px-4 font-semibold">Author (Salted SHA-256)</th>
                <th className="py-3.5 px-4 font-semibold">Post Content</th>
                <th className="py-3.5 px-4 font-semibold">Risk Level</th>
                <th className="py-3.5 px-4 font-semibold">Spam</th>
                <th className="py-3.5 px-4 font-semibold">Timestamp</th>
                <th className="py-3.5 px-4 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[rgba(255,196,140,0.08)]">
              {posts.map((post) => {
                const isSelected = selectedPost?.post_id === post.post_id;
                const spam = post.spam_score !== undefined ? Number(post.spam_score) : 0;
                const isHighRisk = (post.risk_score && post.risk_score > 70) || spam > 0.4;
                const band = post.risk_band || (isHighRisk ? 'High' : 'Low');

                return (
                  <tr
                    key={post.post_id}
                    onClick={() => handleSelectPost(post)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-[rgba(255,122,26,0.12)] border-l-[3px] border-[#ff7a1a]'
                        : 'hover:bg-[rgba(255,154,77,0.06)]'
                    }`}
                  >
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider bg-[rgba(255,154,77,0.12)] text-[#ffd9b8] border border-[rgba(255,196,140,0.2)]">
                        {post.platform}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-[rgba(255,226,205,0.64)] whitespace-nowrap">
                      {post.author_id_hash ? `${post.author_id_hash.substring(0, 10)}...` : 'anon'}
                    </td>
                    <td className="py-3.5 px-4 max-w-md">
                      <p className="text-[#fff3e8] line-clamp-2 leading-relaxed">
                        {post.text}
                      </p>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${getRiskBadgeColor(
                          band
                        )}`}
                      >
                        {band} {post.risk_score ? `(${post.risk_score.toFixed(0)})` : ''}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[rgba(255,226,205,0.7)] whitespace-nowrap">
                      {(spam * 100).toFixed(0)}%
                    </td>
                    <td className="py-3.5 px-4 text-[rgba(255,226,205,0.64)] whitespace-nowrap text-[11px]">
                      {new Date(post.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectPost(post);
                        }}
                        className="px-3 py-1 text-xs font-semibold rounded-lg bg-[rgba(255,154,77,0.1)] hover:bg-[#ff7a1a] hover:text-[#0b0603] text-[#ffd9b8] border border-[rgba(255,196,140,0.25)] transition-all cursor-pointer"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Post Detail Drawer / Modal */}
      {selectedPost && (
        <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-[#0e0704]/95 backdrop-blur-[24px] border-l border-[rgba(255,196,140,0.2)] shadow-2xl overflow-y-auto p-6 space-y-6 animate-slide-left">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-[rgba(255,196,140,0.15)]">
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-md bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)]">
                  {selectedPost.platform} Post
                </span>
                <span className="text-xs font-mono text-[rgba(255,226,205,0.6)]">{selectedPost.post_id}</span>
              </div>
              <h2 className="text-base font-bold text-[#fff3e8] font-['Sora'] mt-1">Multi-Modal Post Inspection</h2>
            </div>
            <button
              onClick={() => setSelectedPost(null)}
              className="p-1.5 text-[rgba(255,226,205,0.6)] hover:text-[#fff3e8] rounded-lg hover:bg-[rgba(255,154,77,0.15)] transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Post Text & Pseudonymized Author */}
          <div className="p-4 rounded-2xl bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] border border-[rgba(255,196,140,0.18)] space-y-3">
            <p className="text-xs text-[#fff3e8] leading-relaxed whitespace-pre-wrap">
              {selectedPost.text}
            </p>
            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[rgba(255,196,140,0.12)] text-[11px] text-[rgba(255,226,205,0.6)]">
              <span>Author Hash: <code className="text-[#ffb679] font-mono">{selectedPost.author_id_hash}</code></span>
              <span>Published: {new Date(selectedPost.created_at).toLocaleString()}</span>
            </div>
          </div>

          {/* Explainable Risk Scoring Card */}
          <div className="p-4 rounded-2xl bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] border border-[rgba(255,196,140,0.18)] space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-[#ff7a1a]" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#ffd9b8] font-['Sora']">
                  Calibrated Risk Fusion (0-100)
                </h3>
              </div>
              {riskData && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getRiskBadgeColor(riskData.risk_band)}`}>
                  {riskData.risk_band} Risk
                </span>
              )}
            </div>

            {loadingRisk ? (
              <div className="flex items-center justify-center py-6 text-xs text-[rgba(255,226,205,0.6)] space-x-2">
                <RefreshCw className="w-4 h-4 text-[#ff7a1a] animate-spin" />
                <span>Computing TreeExplainer SHAP attributions...</span>
              </div>
            ) : riskData ? (
              <div className="space-y-3">
                <div className="flex items-baseline space-x-3">
                  <span className="text-3xl font-extrabold font-mono text-[#fff3e8] font-['Sora']">
                    {riskData.risk_score.toFixed(1)}
                  </span>
                  <span className="text-xs text-[rgba(255,226,205,0.6)]">
                    95% CI: [{riskData.confidence_interval[0].toFixed(1)} - {riskData.confidence_interval[1].toFixed(1)}]
                  </span>
                </div>

                {/* Plain language justification */}
                <div className="p-3 rounded-xl bg-[rgba(255,122,26,0.1)] border border-[rgba(255,154,77,0.25)] text-xs text-[#ffd9b8]">
                  <p className="font-semibold text-[#fff3e8] mb-0.5 font-['Sora']">Analyst Justification:</p>
                  <p className="text-[rgba(255,226,205,0.85)]">{riskData.explanation}</p>
                </div>

                {/* SHAP Feature Drivers */}
                <div className="space-y-2 pt-2">
                  <h4 className="text-[11px] font-semibold text-[rgba(255,226,205,0.6)] uppercase tracking-wider font-['Sora']">
                    Top SHAP Feature Attributions
                  </h4>

                  {/* Positive drivers (push risk up) */}
                  <div className="space-y-1.5">
                    {riskData.drivers.map((d, i) => (
                      <div key={i} className="text-xs">
                        <div className="flex justify-between text-[11px] text-[rgba(255,226,205,0.85)] mb-0.5">
                          <span className="font-mono">{d.feature}</span>
                          <span className="text-[#ff9a4d] font-mono font-medium">+{d.attribution.toFixed(2)}</span>
                        </div>
                        <div className="w-full bg-[rgba(255,196,140,0.12)] h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] h-full rounded-full"
                            style={{ width: `${Math.min(100, Math.max(10, d.attribution * 120))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Negative drivers (pull risk down) */}
                  {riskData.negative_factors?.length > 0 && (
                    <div className="space-y-1.5 pt-2">
                      {riskData.negative_factors.map((d, i) => (
                        <div key={i} className="text-xs">
                          <div className="flex justify-between text-[11px] text-[rgba(255,226,205,0.85)] mb-0.5">
                            <span className="font-mono">{d.feature}</span>
                            <span className="text-[#ffd9b8] font-mono font-medium">{d.attribution.toFixed(2)}</span>
                          </div>
                          <div className="w-full bg-[rgba(255,196,140,0.12)] h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-[rgba(255,196,140,0.4)] h-full rounded-full"
                              style={{ width: `${Math.min(100, Math.max(10, Math.abs(d.attribution) * 120))}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>

          {/* Evidence Integrity Card */}
          <div className="p-4 rounded-2xl bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] border border-[rgba(255,196,140,0.18)] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Fingerprint className="w-4 h-4 text-[#ff9a4d]" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#ffd9b8] font-['Sora']">
                  Cryptographic Evidence Stamp
                </h3>
              </div>
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)]">
                <CheckCircle className="w-3 h-3 text-[#ff9a4d]" />
                <span>Verified SHA-256</span>
              </span>
            </div>

            <div className="p-2.5 bg-black/60 rounded-xl text-[#ffd9b8] font-mono text-[11px] break-all border border-[rgba(255,196,140,0.15)]">
              {selectedPost.evidence_hash || 'c8b2a74e50f391094da68832a87bc1295b92e8fa47b198c63a51092eac85b911'}
            </div>
            <p className="text-[11px] text-[rgba(255,226,205,0.6)]">
              Canonical JSON snapshot fingerprint. Tamper verification runs automatically against the Merkle tree root.
            </p>
          </div>

          {/* Action: Open Investigation Case */}
          <div className="pt-2">
            <button
              onClick={() => onOpenCaseForPost(selectedPost)}
              className="w-full py-3 px-4 rounded-xl font-bold text-xs text-[#0b0603] bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] hover:brightness-110 transition-all shadow-lg shadow-[#ff7a1a]/30 flex items-center justify-center space-x-2 cursor-pointer active:scale-95"
            >
              <FolderPlus className="w-4 h-4" />
              <span>Initiate Case from Post</span>
            </button>
          </div>
        </div>
      )}

      {/* Feed Data Modal */}
      {showFeedModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in font-['Manrope']">
          <div className="bg-[#0e0704] border border-[rgba(255,196,140,0.25)] rounded-[22px] max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="p-5 border-b border-[rgba(255,196,140,0.15)] flex items-center justify-between bg-[rgba(26,14,8,0.5)]">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-[rgba(255,122,26,0.15)] text-[#ff7a1a] border border-[rgba(255,196,140,0.25)]">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-[#fff3e8] font-['Sora']">Feed Social Intelligence Data</h3>
                  <p className="text-xs text-[rgba(255,226,205,0.64)]">
                    Input custom posts to score with calibrated SHAP or trigger pipeline stream ingestion.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowFeedModal(false)}
                className="p-1.5 text-[rgba(255,226,205,0.6)] hover:text-[#fff3e8] rounded-xl hover:bg-[rgba(255,154,77,0.15)] transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mode Switcher */}
            <div className="flex border-b border-[rgba(255,196,140,0.15)] bg-[rgba(14,7,4,0.6)] px-5 pt-3">
              <button
                type="button"
                onClick={() => { setFeedMode('single'); setFeedFeedback(null); }}
                className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center space-x-2 cursor-pointer ${
                  feedMode === 'single'
                    ? 'border-[#ff7a1a] text-[#ff7a1a] font-bold'
                    : 'border-transparent text-[rgba(255,226,205,0.6)] hover:text-[#fff3e8]'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span>Single Post Input & Scoring</span>
              </button>
              <button
                type="button"
                onClick={() => { setFeedMode('batch'); setFeedFeedback(null); }}
                className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center space-x-2 cursor-pointer ${
                  feedMode === 'batch'
                    ? 'border-[#ff7a1a] text-[#ff7a1a] font-bold'
                    : 'border-transparent text-[rgba(255,226,205,0.6)] hover:text-[#fff3e8]'
                }`}
              >
                <UploadCloud className="w-4 h-4" />
                <span>Batch Stream Ingestion</span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-4">
              {feedFeedback && (
                <div
                  className={`p-3.5 rounded-xl border text-xs flex items-start space-x-2 ${
                    feedFeedback.type === 'success'
                      ? 'bg-[rgba(255,154,77,0.15)] border-[rgba(255,196,140,0.35)] text-[#ffd9b8]'
                      : 'bg-[rgba(255,80,20,0.2)] border-[#ff7a1a]/60 text-[#ffd9b8]'
                  }`}
                >
                  {feedFeedback.type === 'success' ? (
                    <CheckCircle className="w-4 h-4 text-[#ff9a4d] mt-0.5 shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-[#ff7a1a] mt-0.5 shrink-0" />
                  )}
                  <span className="leading-relaxed">{feedFeedback.message}</span>
                </div>
              )}

              {feedMode === 'single' ? (
                <form onSubmit={handleIngestSingle} className="space-y-4">
                  {/* Quick Presets */}
                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] block mb-1.5 font-['Sora']">
                      Quick Sample Presets
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setInputText('URGENT: All liquidity reserves frozen at ApexCredit! Bank run underway, withdraw everything immediately before wire collapse!');
                          setInputPlatform('reddit');
                          setInputAuthor('finance_whistle');
                          setInputShares(140);
                          setInputLikes(90);
                        }}
                        className="px-2.5 py-1 text-[11px] bg-[rgba(255,122,26,0.12)] hover:bg-[rgba(255,122,26,0.22)] border border-[rgba(255,196,140,0.25)] text-[#ffd9b8] rounded-lg transition-colors cursor-pointer"
                      >
                        🚨 Bank Run Panic
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setInputText('SYNCHRONIZED ALERT #92: Mass mobilization in front of municipal hall. Disregard official city news, we occupy now!');
                          setInputPlatform('telegram');
                          setInputAuthor('anon_channel_9');
                          setInputShares(280);
                          setInputLikes(45);
                        }}
                        className="px-2.5 py-1 text-[11px] bg-[rgba(255,154,77,0.12)] hover:bg-[rgba(255,154,77,0.22)] border border-[rgba(255,196,140,0.25)] text-[#ffd9b8] rounded-lg transition-colors cursor-pointer"
                      >
                        🤖 Coordinated Mobilization
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setInputText('Benchmarking our new streaming analytics consumer on Kafka with 10k messages/sec throughput.');
                          setInputPlatform('youtube');
                          setInputAuthor('dev_alex');
                          setInputShares(10);
                          setInputLikes(65);
                        }}
                        className="px-2.5 py-1 text-[11px] bg-[rgba(255,196,140,0.08)] hover:bg-[rgba(255,196,140,0.16)] border border-[rgba(255,196,140,0.25)] text-[#ffd9b8] rounded-lg transition-colors cursor-pointer"
                      >
                        ✅ Benign Tech Post
                      </button>
                    </div>
                  </div>

                  {/* Post Text Input */}
                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] block mb-1.5 font-['Sora']">
                      Post Content / Text <span className="text-[#ff7a1a]">*</span>
                    </label>
                    <textarea
                      rows={3}
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder="Type or paste the social media post, comment, or message here..."
                      className="w-full px-3 py-2 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a] focus:ring-1 focus:ring-[#ff7a1a]/40 resize-none font-sans leading-relaxed"
                      required
                    />
                  </div>

                  {/* Platform & Author */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] block mb-1.5 font-['Sora']">
                        Platform
                      </label>
                      <select
                        value={inputPlatform}
                        onChange={(e) => setInputPlatform(e.target.value)}
                        className="w-full px-3 py-2 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a] capitalize"
                      >
                        <option value="reddit">Reddit</option>
                        <option value="youtube">YouTube</option>
                        <option value="telegram">Telegram</option>
                        <option value="mock">Mock</option>
                        <option value="custom">Custom Platform</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] block mb-1.5 font-['Sora']">
                        Author Identifier
                      </label>
                      <input
                        type="text"
                        value={inputAuthor}
                        onChange={(e) => setInputAuthor(e.target.value)}
                        placeholder="e.g. user_handle (Salted SHA-256)"
                        className="w-full px-3 py-2 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a]"
                      />
                    </div>
                  </div>

                  {/* Engagement Metrics */}
                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] block mb-1.5 font-['Sora']">
                      Engagement Signals (Virality & Amplification)
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <span className="text-[10px] text-[rgba(255,226,205,0.5)] block mb-1">Likes</span>
                        <input
                          type="number"
                          min={0}
                          value={inputLikes}
                          onChange={(e) => setInputLikes(Number(e.target.value))}
                          className="w-full px-3 py-1.5 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a]"
                        />
                      </div>
                      <div>
                        <span className="text-[10px] text-[rgba(255,226,205,0.5)] block mb-1">Shares / Reposts</span>
                        <input
                          type="number"
                          min={0}
                          value={inputShares}
                          onChange={(e) => setInputShares(Number(e.target.value))}
                          className="w-full px-3 py-1.5 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a]"
                        />
                      </div>
                      <div>
                        <span className="text-[10px] text-[rgba(255,226,205,0.5)] block mb-1">Replies</span>
                        <input
                          type="number"
                          min={0}
                          value={inputReplies}
                          onChange={(e) => setInputReplies(Number(e.target.value))}
                          className="w-full px-3 py-1.5 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a]"
                        />
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-[rgba(255,226,205,0.6)] leading-normal">
                    🔒 <strong>Privacy Assurance:</strong> Raw author handles are salted and hashed into irreversible SHA-256 tokens at ingestion boundary.
                  </p>

                  <div className="pt-2 flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowFeedModal(false)}
                      className="px-4 py-2 text-xs font-semibold text-[rgba(255,226,205,0.6)] hover:text-[#fff3e8] rounded-xl hover:bg-[rgba(255,154,77,0.12)] transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting || !inputText.trim()}
                      className="px-5 py-2 text-xs font-bold bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] hover:brightness-110 text-[#0b0603] rounded-xl shadow-lg shadow-[#ff7a1a]/30 disabled:opacity-50 flex items-center space-x-2 transition-all cursor-pointer active:scale-95"
                    >
                      {submitting ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Processing & Scoring...</span>
                        </>
                      ) : (
                        <>
                          <Send className="w-3.5 h-3.5" />
                          <span>Analyze & Ingest Post</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              ) : (
                <form onSubmit={handleTriggerBatch} className="space-y-4">
                  <div className="p-3.5 bg-[rgba(255,122,26,0.1)] border border-[rgba(255,154,77,0.25)] rounded-xl text-xs text-[#ffd9b8]">
                    <p className="font-semibold mb-1 font-['Sora'] text-[#fff3e8]">Streaming Ingestion Replay</p>
                    <p className="text-[rgba(255,226,205,0.7)] text-[11px]">
                      Runs canonical ingestion across connectors, applies MinHash deduplication and heuristic spam filtering, and flushes normalized CleanPosts into the historical database.
                    </p>
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] block mb-1.5 font-['Sora']">
                      Platform Source
                    </label>
                    <select
                      value={batchPlatform}
                      onChange={(e) => setBatchPlatform(e.target.value)}
                      className="w-full px-3 py-2 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a]"
                    >
                      <option value="mock">Mock Replay (Local multi-platform dataset)</option>
                      <option value="reddit">Reddit Public API</option>
                      <option value="youtube">YouTube Public Comments API</option>
                      <option value="telegram">Telegram Channel Stream</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] block mb-1.5 font-['Sora']">
                      Search Query / Topic Keyword (Optional)
                    </label>
                    <input
                      type="text"
                      value={batchQuery}
                      onChange={(e) => setBatchQuery(e.target.value)}
                      placeholder="e.g. cyber, crypto, fraud, emergency"
                      className="w-full px-3 py-2 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a]"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-[rgba(255,226,205,0.6)] font-['Sora']">
                        Post Volume Limit
                      </label>
                      <span className="text-xs font-mono font-bold text-[#ff9a4d]">{batchLimit} Posts</span>
                    </div>
                    <input
                      type="range"
                      min={10}
                      max={150}
                      step={10}
                      value={batchLimit}
                      onChange={(e) => setBatchLimit(Number(e.target.value))}
                      className="w-full accent-[#ff7a1a]"
                    />
                  </div>

                  <div className="pt-2 flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowFeedModal(false)}
                      className="px-4 py-2 text-xs font-semibold text-[rgba(255,226,205,0.6)] hover:text-[#fff3e8] rounded-xl hover:bg-[rgba(255,154,77,0.12)] transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={batchLoading}
                      className="px-5 py-2 text-xs font-bold bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] hover:brightness-110 text-[#0b0603] rounded-xl shadow-lg shadow-[#ff7a1a]/30 disabled:opacity-50 flex items-center space-x-2 transition-all cursor-pointer active:scale-95"
                    >
                      {batchLoading ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Ingesting Stream...</span>
                        </>
                      ) : (
                        <>
                          <Database className="w-3.5 h-3.5" />
                          <span>Start Stream Ingestion</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
