import React from 'react';
import {
  X,
  Cpu,
  Database,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Terminal
} from 'lucide-react';
import type { ReadinessResponse } from '../types';

interface DiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  readiness: ReadinessResponse | null;
  onRefresh: () => void;
  currentProvider: string;
  currentModel: string;
  onSelectProvider: (provider: string, model: string) => void;
}

export const DiagnosticsModal: React.FC<DiagnosticsModalProps> = ({
  isOpen,
  onClose,
  readiness,
  onRefresh,
  currentProvider,
  currentModel,
  onSelectProvider,
}) => {
  if (!isOpen) return null;

  const llm = readiness?.llm_provider;
  const vectorStore = readiness?.vector_store;
  const db = readiness?.database;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-blue-400" />
            <h2 className="font-semibold text-white text-sm">
              System Diagnostics & Provider Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs text-slate-300">
          {/* Provider Selection */}
          <div>
            <label className="font-semibold text-white block mb-2">
              Active LLM Provider
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'ollama', name: 'Ollama (Local)', model: 'llama3.2' },
                { id: 'anthropic', name: 'Claude (Cloud)', model: 'claude-3-5-sonnet-20241022' },
                { id: 'openai', name: 'OpenAI (Cloud)', model: 'gpt-4o' },
              ].map((p) => {
                const isSelected = currentProvider.toLowerCase() === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => onSelectProvider(p.id, p.model)}
                    className={`p-2.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-500/10 text-white font-medium'
                        : 'border-slate-800 bg-slate-850 hover:bg-slate-800 text-slate-400'
                    }`}
                  >
                    <div className="font-semibold text-[11px]">{p.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono truncate">{p.model}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Service Health Cards */}
          <div className="space-y-3">
            {/* LLM Status */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white flex items-center space-x-1.5">
                  <Cpu className="w-4 h-4 text-blue-400" />
                  <span>LLM Provider Status ({llm?.provider || currentProvider})</span>
                </span>
                {llm?.is_available ? (
                  <span className="flex items-center space-x-1 text-emerald-400 font-mono text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Connected</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 text-amber-400 font-mono text-[11px]">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Unavailable</span>
                  </span>
                )}
              </div>
              <p className="text-slate-400 text-[11px]">
                Active model: <code className="text-blue-300 font-mono">{llm?.model || currentModel}</code>
              </p>
              {llm?.error && (
                <div className="mt-2 p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]">
                  {llm.error}
                </div>
              )}
              {!llm?.is_available && currentProvider === 'ollama' && (
                <div className="mt-2 p-2.5 rounded bg-slate-900 border border-slate-800 space-y-1 text-[11px] text-slate-400">
                  <div className="flex items-center space-x-1 text-slate-300 font-medium">
                    <Terminal className="w-3.5 h-3.5 text-blue-400" />
                    <span>How to start Ollama locally:</span>
                  </div>
                  <pre className="bg-slate-950 p-1.5 rounded font-mono text-[10px] text-blue-400">
                    ollama serve
                  </pre>
                  <pre className="bg-slate-950 p-1.5 rounded font-mono text-[10px] text-blue-400">
                    ollama pull llama3.2
                  </pre>
                </div>
              )}
            </div>

            {/* Knowledge Base Status */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white flex items-center space-x-1.5">
                  <BookOpen className="w-4 h-4 text-indigo-400" />
                  <span>Transcript Knowledge Base</span>
                </span>
                <span className="text-emerald-400 font-mono text-[11px] flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{vectorStore?.total_chunks || 0} Chunks</span>
                </span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Indexed from Lenny's Podcast transcripts with speaker timestamps and direct YouTube links.
              </p>
            </div>

            {/* Database Status */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white flex items-center space-x-1.5">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span>Database Persistence</span>
                </span>
                <span className="text-emerald-400 font-mono text-[11px] flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{db || 'Connected'}</span>
                </span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Sessions, message histories, and artifacts are strictly isolated by session ID.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <button
            onClick={onRefresh}
            className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Recheck Health</span>
          </button>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
