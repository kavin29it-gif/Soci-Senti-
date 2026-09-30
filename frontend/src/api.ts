import type {
  AuditVerification,
  Case,
  CaseItem,
  CaseNote,
  DashboardOverview,
  MerkleProof,
  ModelHealth,
  NetworkLink,
  NetworkNode,
  CoordinatedCluster,
  Post,
  RiskAnalysis,
  TimelineEvent,
  TopicNarrative,
} from './types';


const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const cleanUrl = url.startsWith('/') ? url : `/${url}`;
  const res = await fetch(`${API_BASE}${cleanUrl}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const errorText = await res.text();
    let msg = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.detail) msg = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
    } catch {
      // use raw errorText
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // System Health
  async getHealth(): Promise<{ status: string; service: string; version: string }> {
    return fetchJson('/health');
  },

  // Overview
  async getOverview(): Promise<DashboardOverview> {
    return fetchJson('/dashboard/overview');
  },

  // Posts Exploration
  async getPosts(params?: { platform?: string; limit?: number; search?: string }): Promise<{ count: number; posts: Post[] }> {
    const q = new URLSearchParams();
    if (params?.platform && params.platform !== 'all') q.set('platform', params.platform);
    if (params?.limit) q.set('limit', params.limit.toString());
    if (params?.search) q.set('search', params.search);
    return fetchJson(`/posts?${q.toString()}`);
  },

  // Feed / Ingest Data
  async ingestPost(data: {
    text: string;
    platform?: string;
    author_handle?: string;
    likes?: number;
    shares?: number;
    replies?: number;
  }): Promise<{ status: string; post: Post; risk_analysis: RiskAnalysis }> {
    return fetchJson('/ingest/post', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async triggerIngest(data: {
    platform: string;
    limit?: number;
    query?: string;
  }): Promise<{ platform: string; fetched: number; clean_emitted: number; duplicates: number; spam_dropped: number; elapsed_seconds: number }> {
    return fetchJson('/ingest/trigger', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Explainable Risk Scoring
  async getRiskAnalysis(entityType: string, entityId: string): Promise<RiskAnalysis> {
    return fetchJson(`/risk/${entityType}/${encodeURIComponent(entityId)}`);
  },

  // Case Management
  async getCases(status?: string, priority?: string): Promise<{ cases: Case[] }> {
    const q = new URLSearchParams();
    if (status && status !== 'all') q.set('status', status);
    if (priority && priority !== 'all') q.set('priority', priority);
    return fetchJson(`/cases?${q.toString()}`);
  },

  async getCaseDetails(caseId: string): Promise<{ case: Case; items: CaseItem[]; notes: CaseNote[]; merkle_root: string }> {
    return fetchJson(`/cases/${caseId}`);
  },

  async createCase(data: {
    title: string;
    description: string;
    priority: string;
    entity_type?: string;
    entity_id?: string;
    created_by?: string;
  }): Promise<Case> {
    return fetchJson('/cases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateCaseStatus(caseId: string, status: string, userId: string = 'analyst@socisenti.local'): Promise<Case> {
    return fetchJson(`/cases/${caseId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, user_id: userId }),
    });
  },

  async approveCase(caseId: string, reviewerId: string = 'reviewer@socisenti.local'): Promise<{ status: string; case: Case }> {
    return fetchJson(`/cases/${caseId}/approve?reviewer_id=${encodeURIComponent(reviewerId)}`, {
      method: 'POST',
    });
  },

  async getCaseTimeline(caseId: string): Promise<{ case_id: string; timeline: TimelineEvent[] }> {
    return fetchJson(`/cases/${caseId}/timeline`);
  },

  async addCaseNote(caseId: string, note: string, authorId: string = 'analyst@socisenti.local'): Promise<CaseNote> {
    return fetchJson(`/cases/${caseId}/notes`, {
      method: 'POST',
      body: JSON.stringify({ note, author_id: authorId }),
    });
  },

  async attachCaseItem(caseId: string, itemType: string, itemId: string, addedBy: string = 'analyst@socisenti.local'): Promise<CaseItem> {
    return fetchJson(`/cases/${caseId}/items`, {
      method: 'POST',
      body: JSON.stringify({ item_type: itemType, item_id: itemId, added_by: addedBy }),
    });
  },

  getPdfUrl(caseId: string): string {
    return `${API_BASE}/cases/${caseId}/export/pdf`;
  },

  async getStrDraft(caseId: string): Promise<Record<string, unknown>> {
    return fetchJson(`/cases/${caseId}/export/str`);
  },

  // Network Engine
  async getNetworkGraph(): Promise<{
    node_count: number;
    edge_count: number;
    community_count: number;
    nodes: NetworkNode[];
    links: NetworkLink[];
    coordinated_clusters: CoordinatedCluster[];
  }> {
    return fetchJson('/analytics/network');
  },

  // Topics / Narratives
  async getTopics(): Promise<{ total_posts_analyzed: number; topics: TopicNarrative[] }> {
    return fetchJson('/analytics/topics');
  },

  // Evidence & Cryptographic Audit
  async verifyAudit(): Promise<AuditVerification> {
    return fetchJson('/audit/verify');
  },

  async verifyEvidence(evidence: {
    entity_type: string;
    entity_id: string;
    source_url: string;
    content_snapshot: string;
    fetched_at: string;
    sha256: string;
  }): Promise<{ verified: boolean; sha256: string; message: string }> {
    return fetchJson('/evidence/verify', {
      method: 'POST',
      body: JSON.stringify(evidence),
    });
  },

  async getMerkleProof(entityId: string): Promise<MerkleProof> {
    return fetchJson(`/evidence/${encodeURIComponent(entityId)}/proof`);
  },

  // Model Health & Drift
  async getModelHealth(): Promise<ModelHealth> {
    return fetchJson('/ml/health');
  },

  // Copilot Query (returns 501)
  async queryCopilot(prompt: string): Promise<{ response?: string }> {
    return fetchJson('/copilot/query', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  },
};
