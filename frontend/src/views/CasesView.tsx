import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  FileCode,
  FolderLock,
  Plus,
  RefreshCw,
  Send,
  Shield,
  ShieldCheck,
  X
} from 'lucide-react';
import { api } from '../api';
import type { Case, CaseItem, CaseNote, TimelineEvent, UserRole } from '../types';

interface CasesViewProps {
  role: UserRole;
  prefillEntity?: { entityType: string; entityId: string } | null;
  onClearPrefill?: () => void;
}

export const CasesView: React.FC<CasesViewProps> = ({ role, prefillEntity, onClearPrefill }) => {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [items, setItems] = useState<CaseItem[]>([]);
  const [notes, setNotes] = useState<CaseNote[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [merkleRoot, setMerkleRoot] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);


  // Form states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newPriority, setNewPriority] = useState('medium');
  const [newNote, setNewNote] = useState('');
  const [newItemType, setNewItemType] = useState('post');
  const [newItemId, setNewItemId] = useState('');
  const [showStrModal, setShowStrModal] = useState(false);
  const [strContent, setStrContent] = useState<string>('');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await api.getCases();
      setCases(res.cases || []);
      if (res.cases && res.cases.length > 0 && !selectedCase) {
        handleSelectCase(res.cases[0]);
      }
    } catch {
      // Mock fallback cases
      const fallback: Case[] = [
        {
          case_id: 'case_cib_8820',
          title: 'Coordinated Liquidity Run on ApexReserve',
          description: 'Multi-account burst detected across Reddit and Telegram amplifying insolvency claims.',
          status: 'investigating',
          priority: 'high',
          assigned_to: 'analyst@socisenti.local',
          created_by: 'analyst@socisenti.local',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_approved: false,
          entity_type: 'cluster',
          entity_id: 'cluster_001',
        },
      ];
      setCases(fallback);
      handleSelectCase(fallback[0]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCase = async (c: Case) => {
    setSelectedCase(c);
    setErrorMsg(null);
    try {
      const details = await api.getCaseDetails(c.case_id);
      setSelectedCase(details.case);
      setItems(details.items || []);
      setNotes(details.notes || []);
      setMerkleRoot(details.merkle_root || '');

      const tl = await api.getCaseTimeline(c.case_id);
      setTimeline(tl.timeline || []);
    } catch {
      // Mock details fallback
      setItems([
        { id: 'item_1', item_type: 'cluster', item_id: 'cluster_001', added_by: 'analyst', added_at: new Date().toISOString() },
        { id: 'item_2', item_type: 'post', item_id: 'tg_post_49201', added_by: 'analyst', added_at: new Date().toISOString() },
      ]);
      setNotes([
        { id: 'n1', author_id: 'analyst@socisenti.local', note: 'Initial evidence gathered from Telegram channel leak.', created_at: new Date().toISOString() },
      ]);
      setTimeline([
        { timestamp: new Date().toISOString(), type: 'case_created', description: 'Case opened by analyst', user: 'analyst@socisenti.local' },
        { timestamp: new Date().toISOString(), type: 'item_attached', description: 'Attached cluster_001', user: 'analyst@socisenti.local' },
      ]);
      setMerkleRoot('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  // Handle prefill if opened from Overview or Explore
  useEffect(() => {
    if (prefillEntity) {
      setNewTitle(`Investigation into ${prefillEntity.entityType}: ${prefillEntity.entityId}`);
      setNewDescription(`Flagged suspicious behavior detected for ${prefillEntity.entityType} with ID ${prefillEntity.entityId}.`);
      setShowCreateModal(true);
    }
  }, [prefillEntity]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await api.createCase({
        title: newTitle,
        description: newDescription,
        priority: newPriority,
        entity_type: prefillEntity?.entityType,
        entity_id: prefillEntity?.entityId,
      });
      setShowCreateModal(false);
      setNewTitle('');
      setNewDescription('');
      if (onClearPrefill) onClearPrefill();
      await fetchCases();
      handleSelectCase(created);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(`Failed to create case: ${msg}`);
    }
  };

  const handleUpdateStatus = async (status: string) => {
    if (!selectedCase) return;
    setErrorMsg(null);
    try {
      const updated = await api.updateCaseStatus(selectedCase.case_id, status, `${role}@socisenti.local`);
      setSelectedCase(updated);
      await fetchCases();
      const tl = await api.getCaseTimeline(selectedCase.case_id);
      setTimeline(tl.timeline || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(msg);
    }
  };

  const handleApproveCase = async () => {
    if (!selectedCase) return;
    setErrorMsg(null);
    try {
      const res = await api.approveCase(selectedCase.case_id, `${role}@socisenti.local`);
      setSelectedCase(res.case);
      await fetchCases();
      const tl = await api.getCaseTimeline(selectedCase.case_id);
      setTimeline(tl.timeline || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(msg);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || !newNote.trim()) return;
    try {
      const note = await api.addCaseNote(selectedCase.case_id, newNote, `${role}@socisenti.local`);
      setNotes([...notes, note]);
      setNewNote('');
      const tl = await api.getCaseTimeline(selectedCase.case_id);
      setTimeline(tl.timeline || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(msg);
    }
  };

  const handleAttachItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || !newItemId.trim()) return;
    try {
      const item = await api.attachCaseItem(selectedCase.case_id, newItemType, newItemId, `${role}@socisenti.local`);
      setItems([...items, item]);
      setNewItemId('');
      const tl = await api.getCaseTimeline(selectedCase.case_id);
      setTimeline(tl.timeline || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(msg);
    }
  };

  const handleExportStr = async () => {
    if (!selectedCase) return;
    try {
      const str = await api.getStrDraft(selectedCase.case_id);
      setStrContent(JSON.stringify(str, null, 2));
      setShowStrModal(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(msg);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'closed':
        return 'bg-[rgba(255,196,140,0.08)] text-[rgba(255,226,205,0.7)] border-[rgba(255,196,140,0.2)]';
      case 'review':
        return 'bg-[rgba(255,154,77,0.18)] text-[#ffb679] border-[#ff9a4d]/60';
      case 'investigating':
        return 'bg-[rgba(255,122,26,0.22)] text-[#ffd9b8] border-[#ff7a1a] shadow-[0_0_12px_rgba(255,122,26,0.3)]';
      default:
        return 'bg-[rgba(255,182,121,0.15)] text-[#ffd9b8] border-[rgba(255,196,140,0.3)]';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12 font-['Manrope']">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#fff3e8] font-['Sora'] flex items-center space-x-2">
            <span>Case Management & Compliance Workflow</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)]">
              Layer 5
            </span>
          </h1>
          <p className="text-xs text-[rgba(255,226,205,0.64)] mt-1">
            Investigation dossiers, chronological timeline, reviewer approval gates, and compliance PDF/STR exports.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-2 px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] text-[#0b0603] hover:brightness-110 shadow-lg shadow-[#ff7a1a]/30 transition-all self-start sm:self-auto cursor-pointer active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>New Case</span>
        </button>
      </div>

      {errorMsg && (
        <div className="p-3.5 rounded-2xl bg-[rgba(255,80,20,0.15)] border border-[#ff7a1a]/40 text-xs text-[#ffd9b8] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-[#ff7a1a] shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="p-1 hover:text-white cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Grid: Cases List on Left, Case Details on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Cases List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-[rgba(255,226,205,0.6)] px-1 font-['Sora'] font-semibold">
            <span>Cases ({cases.length})</span>
            <button onClick={fetchCases} className="hover:text-white flex items-center space-x-1 cursor-pointer">
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-[#ff7a1a]' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="space-y-2 max-h-[750px] overflow-y-auto pr-1">
            {cases.map((c) => {
              const isSelected = selectedCase?.case_id === c.case_id;
              return (
                <div
                  key={c.case_id}
                  onClick={() => handleSelectCase(c)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'glass-panel border-l-[3px] border-[#ff7a1a] bg-[rgba(255,122,26,0.12)] shadow-md shadow-[#ff7a1a]/20'
                      : 'glass-panel hover:bg-[rgba(255,154,77,0.06)]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs text-[rgba(255,226,205,0.6)]">{c.case_id}</span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(
                        c.status
                      )}`}
                    >
                      {c.status}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-[#fff3e8] font-['Sora'] line-clamp-1">{c.title}</h3>
                  <p className="text-xs text-[rgba(255,226,205,0.6)] line-clamp-2 mt-1">{c.description}</p>

                  <div className="flex items-center justify-between pt-3 mt-3 border-t border-[rgba(255,196,140,0.12)] text-[11px] text-[rgba(255,226,205,0.6)]">
                    <span className="capitalize text-[#ffd9b8]">Priority: {c.priority}</span>
                    {c.is_approved && (
                      <span className="flex items-center space-x-1 text-[#ffd9b8] font-semibold">
                        <CheckCircle2 className="w-3 h-3 text-[#ff9a4d]" />
                        <span>Reviewer Approved</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 2 Columns: Selected Case Detail */}
        {selectedCase ? (
          <div className="lg:col-span-2 space-y-6">
            {/* Case Overview Card */}
            <div className="glass-panel p-6 rounded-[22px] space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-mono text-xs text-[#ff9a4d] font-bold">{selectedCase.case_id}</span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(
                        selectedCase.status
                      )}`}
                    >
                      {selectedCase.status}
                    </span>
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-[rgba(255,154,77,0.12)] text-[#ffd9b8] border border-[rgba(255,196,140,0.25)]">
                      {selectedCase.priority} priority
                    </span>
                  </div>
                  <h2 className="text-lg font-extrabold text-[#fff3e8] font-['Sora']">{selectedCase.title}</h2>
                  <p className="text-xs text-[rgba(255,226,205,0.85)] mt-1 leading-relaxed">
                    {selectedCase.description}
                  </p>
                </div>

                {/* Export Buttons */}
                <div className="flex flex-wrap items-center gap-2 self-start">
                  <a
                    href={api.getPdfUrl(selectedCase.case_id)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-bold rounded-xl bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] text-[#0b0603] hover:brightness-110 shadow-md shadow-[#ff7a1a]/30 transition-all cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download PDF Dossier</span>
                  </a>

                  <button
                    onClick={handleExportStr}
                    className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-[rgba(255,154,77,0.08)] hover:bg-[rgba(255,154,77,0.16)] text-[#fff3e8] border border-[rgba(255,196,140,0.25)] transition-all cursor-pointer"
                  >
                    <FileCode className="w-3.5 h-3.5 text-[#ff9a4d]" />
                    <span>STR Draft JSON</span>
                  </button>
                </div>
              </div>

              {/* Status Transitions & Reviewer Approval Step */}
              <div className="p-4 rounded-xl bg-[rgba(14,7,4,0.6)] border border-[rgba(255,196,140,0.15)] flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2 text-xs">
                  <span className="text-[rgba(255,226,205,0.6)] font-semibold font-['Sora']">Status Transition:</span>
                  {(['open', 'investigating', 'review', 'closed'] as const).map((s) => (
                    <button
                      key={s}
                      onClick={() => handleUpdateStatus(s)}
                      disabled={selectedCase.status === s}
                      className={`px-3 py-1 rounded-lg capitalize font-semibold transition-all cursor-pointer ${
                        selectedCase.status === s
                          ? 'bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603] cursor-default font-bold shadow-sm shadow-[#ff7a1a]/30'
                          : 'bg-[rgba(255,154,77,0.08)] border border-[rgba(255,196,140,0.2)] text-[rgba(255,226,205,0.7)] hover:text-white hover:bg-[rgba(255,154,77,0.15)]'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>

                {/* Reviewer Approval Action */}
                <div className="flex items-center space-x-2">
                  {selectedCase.is_approved ? (
                    <div className="flex items-center space-x-1.5 text-xs text-[#ffd9b8] font-bold">
                      <ShieldCheck className="w-4 h-4 text-[#ff9a4d]" />
                      <span>Approved by {selectedCase.approved_by || 'Reviewer'}</span>
                    </div>
                  ) : (
                    <button
                      onClick={handleApproveCase}
                      className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-bold rounded-xl bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603] hover:brightness-110 shadow-md shadow-[#ff7a1a]/30 transition-all cursor-pointer"
                    >
                      <FileCheck className="w-3.5 h-3.5" />
                      <span>Approve Case (Reviewer)</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Merkle Root Hash badge */}
              <div className="p-3 bg-black/60 rounded-xl border border-[rgba(255,196,140,0.15)] flex items-center justify-between text-[11px] text-[rgba(255,226,205,0.6)]">
                <span className="flex items-center space-x-1.5">
                  <Shield className="w-3.5 h-3.5 text-[#ff7a1a]" />
                  <span>Case Merkle Root:</span>
                </span>
                <code className="text-[#ffd9b8] font-mono text-[10px] break-all">
                  {merkleRoot || 'Computing Merkle tree...'}
                </code>
              </div>
            </div>

            {/* Sub-grid: Attached Evidence Items & Analyst Notes */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Attached Items */}
              <div className="glass-panel p-5 rounded-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#fff3e8] font-['Sora']">
                    Attached Evidence Items ({items.length})
                  </h3>
                </div>

                {/* Items List */}
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {items.map((it) => (
                    <div
                      key={it.id}
                      className="p-2.5 rounded-xl bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] border border-[rgba(255,196,140,0.18)] text-xs flex items-center justify-between"
                    >
                      <div>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.25)] mr-2">
                          {it.item_type}
                        </span>
                        <span className="font-mono text-[#fff3e8]">{it.item_id}</span>
                      </div>
                      <span className="text-[10px] text-[rgba(255,226,205,0.5)]">
                        {new Date(it.added_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Attach form */}
                <form onSubmit={handleAttachItem} className="pt-2 border-t border-[rgba(255,196,140,0.15)] flex space-x-2">
                  <select
                    value={newItemType}
                    onChange={(e) => setNewItemType(e.target.value)}
                    className="px-2 py-1.5 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a]"
                  >
                    <option value="post">Post</option>
                    <option value="author">Author</option>
                    <option value="cluster">Cluster</option>
                    <option value="evidence">Evidence</option>
                  </select>
                  <input
                    type="text"
                    value={newItemId}
                    onChange={(e) => setNewItemId(e.target.value)}
                    placeholder="Enter ID..."
                    className="flex-1 px-3 py-1.5 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a]"
                  />
                  <button
                    type="submit"
                    className="px-3.5 py-1.5 text-xs font-bold bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] hover:brightness-110 text-[#0b0603] rounded-xl transition-all cursor-pointer shadow-md shadow-[#ff7a1a]/30"
                  >
                    Attach
                  </button>
                </form>
              </div>

              {/* Analyst Notes */}
              <div className="glass-panel p-5 rounded-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#fff3e8] font-['Sora']">
                    Analyst Notes ({notes.length})
                  </h3>
                </div>

                {/* Notes List */}
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {notes.map((n) => (
                    <div
                      key={n.id}
                      className="p-2.5 rounded-xl bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] border border-[rgba(255,196,140,0.18)] text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between text-[10px] text-[rgba(255,226,205,0.5)]">
                        <span className="font-mono text-[#ffb679]">{n.author_id}</span>
                        <span>{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <p className="text-[#fff3e8]">{n.note}</p>
                    </div>
                  ))}
                </div>

                {/* Add Note form */}
                <form onSubmit={handleAddNote} className="pt-2 border-t border-[rgba(255,196,140,0.15)] flex space-x-2">
                  <input
                    type="text"
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder="Add investigation observation..."
                    className="flex-1 px-3 py-1.5 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a]"
                  />
                  <button
                    type="submit"
                    className="p-2 text-xs font-bold bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] hover:brightness-110 text-[#0b0603] rounded-xl transition-all cursor-pointer shadow-md shadow-[#ff7a1a]/30"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </div>

            {/* Chronological Investigation Timeline */}
            <div className="glass-panel p-6 rounded-[22px] space-y-4">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-[#ff7a1a]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#fff3e8] font-['Sora']">
                  Chronological Audit Timeline
                </h3>
              </div>

              <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[rgba(255,196,140,0.2)]">
                {timeline.map((ev, idx) => (
                  <div key={idx} className="relative text-xs">
                    <span className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-[#ff7a1a] ring-4 ring-[#0b0603]" />
                    <div className="flex items-center justify-between text-[11px] text-[rgba(255,226,205,0.5)]">
                      <span className="font-mono text-[#ffd9b8] uppercase text-[10px] font-bold">{ev.type}</span>
                      <span>{new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                    </div>
                    <p className="text-[#fff3e8] font-medium mt-0.5">{ev.description}</p>
                    <p className="text-[10px] text-[rgba(255,226,205,0.5)] mt-0.5">by {ev.user}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="lg:col-span-2 p-12 rounded-[22px] glass-panel text-center text-[rgba(255,226,205,0.6)] flex flex-col items-center justify-center space-y-3">
            <FolderLock className="w-10 h-10 text-[rgba(255,154,77,0.4)]" />
            <p className="text-sm font-semibold text-[#fff3e8]">Select a case from the left list or create a new investigation.</p>
          </div>
        )}
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in font-['Manrope']">
          <div className="w-full max-w-lg bg-[#0e0704] border border-[rgba(255,196,140,0.25)] rounded-[22px] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[rgba(255,196,140,0.15)]">
              <h3 className="text-base font-extrabold text-[#fff3e8] font-['Sora']">Create New Investigation Case</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1.5 text-[rgba(255,226,205,0.6)] hover:text-white rounded-lg hover:bg-[rgba(255,154,77,0.15)] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
              <div>
                <label className="block text-[#ffd9b8] font-semibold mb-1 font-['Sora']">Case Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Coordinated Liquidity Attack Investigation"
                  className="w-full px-3 py-2 bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a]"
                />
              </div>

              <div>
                <label className="block text-[#ffd9b8] font-semibold mb-1 font-['Sora']">Description</label>
                <textarea
                  rows={3}
                  required
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Detailed rationale for opening this investigation..."
                  className="w-full px-3 py-2 bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] placeholder-[rgba(255,226,205,0.4)] focus:outline-none focus:border-[#ff7a1a]"
                />
              </div>

              <div>
                <label className="block text-[#ffd9b8] font-semibold mb-1 font-['Sora']">Priority</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="w-full px-3 py-2 bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a]"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-[rgba(255,196,140,0.15)]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-[rgba(255,154,77,0.08)] hover:bg-[rgba(255,154,77,0.16)] text-[rgba(255,226,205,0.7)] hover:text-white rounded-xl font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] hover:brightness-110 text-[#0b0603] rounded-xl font-bold shadow-md shadow-[#ff7a1a]/30 cursor-pointer active:scale-95"
                >
                  Create Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* STR Draft Modal */}
      {showStrModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in font-['Manrope']">
          <div className="w-full max-w-2xl bg-[#0e0704] border border-[rgba(255,196,140,0.25)] rounded-[22px] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[rgba(255,196,140,0.15)]">
              <div className="flex items-center space-x-2">
                <FileCode className="w-5 h-5 text-[#ff7a1a]" />
                <h3 className="text-base font-extrabold text-[#fff3e8] font-['Sora']">Suspicious Activity Report (STR) Draft Template</h3>
              </div>
              <button
                onClick={() => setShowStrModal(false)}
                className="p-1.5 text-[rgba(255,226,205,0.6)] hover:text-white rounded-xl hover:bg-[rgba(255,154,77,0.15)] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3.5 bg-[rgba(255,122,26,0.1)] border border-[rgba(255,154,77,0.25)] rounded-xl text-xs text-[#ffd9b8]">
              Regulatory Note: This document is an automated <strong>draft template</strong> generated from fused multimodal signals for human analyst review. It is not an official regulatory filing.
            </div>

            <pre className="p-4 bg-black/60 rounded-xl text-[#ffd9b8] font-mono text-xs max-h-96 overflow-y-auto whitespace-pre-wrap border border-[rgba(255,196,140,0.15)]">
              {strContent}
            </pre>

            <div className="flex justify-end pt-3 border-t border-[rgba(255,196,140,0.15)]">
              <button
                onClick={() => setShowStrModal(false)}
                className="px-4 py-2 bg-[rgba(255,154,77,0.08)] hover:bg-[rgba(255,154,77,0.16)] text-[#fff3e8] rounded-xl text-xs font-semibold cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
