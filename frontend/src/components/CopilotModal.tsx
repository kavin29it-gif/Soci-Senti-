import React, { useState } from 'react';
import { Bot, X, Sparkles, AlertCircle, ArrowRight } from 'lucide-react';
import { api } from '../api';

interface CopilotModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CopilotModal: React.FC<CopilotModalProps> = ({ isOpen, onClose }) => {
  const [prompt, setPrompt] = useState('Find all coordinated sockpuppet clusters active in the liquidity run on ApexReserve');
  const [loading, setLoading] = useState(false);
  const [responseInfo, setResponseInfo] = useState<{ status: number; text: string } | null>(null);

  if (!isOpen) return null;

  const handleTestQuery = async () => {
    setLoading(true);
    setResponseInfo(null);
    try {
      await api.queryCopilot(prompt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setResponseInfo({
        status: 501,
        text: msg,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in font-['Manrope']">
      <div className="relative w-full max-w-xl bg-[#0e0704] border border-[rgba(255,196,140,0.25)] rounded-[22px] shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,196,140,0.15)] bg-[rgba(26,14,8,0.5)]">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-[rgba(255,122,26,0.15)] text-[#ff7a1a] border border-[rgba(255,196,140,0.25)]">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-extrabold text-[#fff3e8] font-['Sora']">Investigative AI Copilot</h3>
                <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.3)] rounded-full">
                  v2 Roadmap Stub
                </span>
              </div>
              <p className="text-xs text-[rgba(255,226,205,0.64)]">Natural-Language Social Network Analysis & Querying</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[rgba(255,226,205,0.6)] hover:text-white rounded-xl hover:bg-[rgba(255,154,77,0.15)] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="p-4 rounded-xl bg-[rgba(255,122,26,0.1)] border border-[rgba(255,154,77,0.25)] text-xs text-[#ffd9b8] flex items-start space-x-3">
            <Sparkles className="w-5 h-5 text-[#ff7a1a] shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-[#fff3e8] mb-1 font-['Sora']">Architecture Specification Note</p>
              <p className="text-[rgba(255,226,205,0.85)] leading-relaxed">
                As defined in Section 3 of the Master PRD, Conversational AI Copilot with dynamic graph traversals is designated for the v2 roadmap. The gateway exposes a formal <code className="px-1.5 py-0.5 bg-black/60 rounded text-[#ffd9b8] font-mono">POST /copilot/query</code> stub returning <strong className="text-[#fff3e8]">HTTP 501 Not Implemented</strong>.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#ffd9b8] mb-1.5 font-['Sora']">
              Simulate Copilot Natural-Language Query:
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="flex-1 px-3 py-2 text-xs bg-[rgba(20,10,5,0.85)] border border-[rgba(255,196,140,0.2)] rounded-xl text-[#fff3e8] focus:outline-none focus:border-[#ff7a1a]"
                placeholder="Ask anything about entities, clusters, or timelines..."
              />
              <button
                onClick={handleTestQuery}
                disabled={loading}
                className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603] hover:brightness-110 disabled:opacity-50 transition-all shadow-md shadow-[#ff7a1a]/30 cursor-pointer active:scale-95"
              >
                <span>{loading ? 'Querying...' : 'Send'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Response output */}
          {responseInfo && (
            <div className="p-4 rounded-xl bg-[rgba(255,122,26,0.12)] border border-[rgba(255,196,140,0.25)] text-xs space-y-2">
              <div className="flex items-center space-x-2 text-[#ff9a4d] font-bold font-['Sora']">
                <AlertCircle className="w-4 h-4 text-[#ff7a1a]" />
                <span>Backend Gateway Response [HTTP {responseInfo.status}]</span>
              </div>
              <pre className="p-3 rounded-xl bg-black/60 text-[#ffd9b8] font-mono text-[11px] whitespace-pre-wrap break-all border border-[rgba(255,196,140,0.15)]">
                {responseInfo.text}
              </pre>
            </div>
          )}

          <div className="border-t border-[rgba(255,196,140,0.15)] pt-3">
            <h4 className="text-xs font-bold text-[#fff3e8] mb-2 font-['Sora']">Planned v2 Capabilities:</h4>
            <ul className="text-xs text-[rgba(255,226,205,0.6)] space-y-1.5 list-disc list-inside">
              <li>Multi-hop graph search across coordinate sockpuppet communities</li>
              <li>Automated timeline generation for novel financial fraud patterns</li>
              <li>Real-time natural language summaries for compliance dossiers</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-[rgba(255,196,140,0.15)] bg-[rgba(26,14,8,0.4)] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-[#fff3e8] bg-[rgba(255,154,77,0.08)] hover:bg-[rgba(255,154,77,0.16)] border border-[rgba(255,196,140,0.2)] rounded-xl transition-all cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
