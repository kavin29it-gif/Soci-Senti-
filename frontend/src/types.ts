export type UserRole = 'analyst' | 'reviewer' | 'admin';

export type RiskBand = 'Low' | 'Medium' | 'High';

export interface Post {
  post_id: string;
  platform: 'reddit' | 'youtube' | 'telegram' | 'mock';
  author_id_hash: string;
  text: string;
  created_at: string;
  spam_score?: number;
  tokens?: string[];
  entities?: Record<string, string[]>;
  emotions?: Record<string, number>;
  sentiment?: {
    label: string;
    score: number;
    negative_prob: number;
    neutral_prob: number;
    positive_prob: number;
  };
  risk_score?: number;
  risk_band?: RiskBand;
  evidence_hash?: string;
}

export interface ShapDriver {
  feature: string;
  attribution: number;
  value: number;
}

export interface RiskAnalysis {
  entity_type: string;
  entity_id: string;
  risk_score: number;
  confidence_interval: [number, number];
  risk_band: RiskBand;
  anomaly_score: number;
  coordination_score: number;
  explanation: string;
  drivers: ShapDriver[];
  negative_factors: ShapDriver[];
}

export interface CaseItem {
  id: string;
  item_type: 'post' | 'author' | 'cluster' | 'evidence';
  item_id: string;
  added_by: string;
  added_at: string;
}

export interface CaseNote {
  id: string;
  author_id: string;
  note: string;
  created_at: string;
}

export interface TimelineEvent {
  timestamp: string;
  type: string;
  description: string;
  user: string;
}

export interface Case {
  case_id: string;
  title: string;
  description: string;
  status: 'open' | 'investigating' | 'review' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assigned_to?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_approved: boolean;
  approved_by?: string;
  approved_at?: string;
  entity_type?: string;
  entity_id?: string;
}

export interface NetworkNode {
  id: string;
  short_id: string;
  platform: string;
  community: number;
  degree: number;
  pagerank: number;
  coordinated: boolean;
  x?: number;
  y?: number;
}

export interface NetworkLink {
  source: string;
  target: string;
  weight: number;
  interaction: string;
}

export interface CoordinatedCluster {
  cluster_id: string;
  account_count: number;
  accounts: string[];
  evidence_post_ids: string[];
  sample_text: string;
  coordination_score: number;
}

export interface TopicNarrative {
  topic_id: number;
  topic_label: string;
  post_count: number;
  percentage: number;
  top_keywords: string[];
  growth_velocity: number;
  forecast_next_24h: number;
  status: 'emerging' | 'surging' | 'stable';
}

export interface AuditVerification {
  valid: boolean;
  total_records: number;
  corrupted_row_id: number | null;
  message: string;
}

export type MerkleProofStep = { position: 'left' | 'right'; hash: string } | [string, 'left' | 'right'];

export interface MerkleProof {
  entity_id: string;
  leaf_hash: string;
  merkle_root: string;
  proof_path: MerkleProofStep[];
  verified: boolean;
}

export interface ModelHealth {
  status: string;
  model_version: string;
  embedder: string;
  overall_psi: number;
  drift_status: string;
  training_baseline_records: number;
  holdout_accuracy: number;
  holdout_f1: number;
  inference_latency_p95_ms: number;
  cache_hit_rate: number;
  feature_drifts: Array<{
    feature: string;
    psi: number;
    status: string;
  }>;
  recent_feedback: Array<{
    date: string;
    precision: number;
    analyst_reviews: number;
  }>;
}

export interface DashboardOverview {
  kpis: {
    posts_ingested: number;
    high_risk_alerts: number;
    open_cases: number;
    verified_evidence_items: number;
  };
  volume_by_platform: Record<string, number>;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  top_emerging_topics: Array<{
    topic: string;
    velocity: number;
    post_count: number;
  }>;
  top_risky_entities: Array<{
    entity_id: string;
    entity_type: string;
    risk_score: number;
    risk_band: RiskBand;
  }>;
}
