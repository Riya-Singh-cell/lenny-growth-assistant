import React from 'react';
import { Sparkles, Cpu, Activity } from 'lucide-react';
import type { ReadinessResponse } from '../types';

interface HeaderProps {
  readiness: ReadinessResponse | null;
  currentProvider: string;
  currentModel: string;
  onSelectProvider: (provider: string, model: string) => void;
  onOpenDiagnostics: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  readiness,
  currentProvider,
  currentModel,
  onOpenDiagnostics,
}) => {
  const isReady = readiness?.status === 'ready';
  const isDegraded = readiness?.status === 'degraded';
  const chunkCount = readiness?.vector_store?.total_chunks || 0;

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-4 flex items-center justify-between select-none z-10">
      {/* Left Brand Area */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-semibold text-sm tracking-tight text-white">
              The Lenny Growth Assistant
            </h1>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Grounded RAG
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            Lenny's Podcast Knowledge Base • {chunkCount} Indexed Chunks
          </p>
        </div>
      </div>

      {/* Right Controls Area */}
      <div className="flex items-center space-x-3">
        {/* Active Model Indicator Button */}
        <button
          onClick={onOpenDiagnostics}
          className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs text-slate-300 transition-colors"
          title="Click to view LLM diagnostics and settings"
        >
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-mono text-[11px] capitalize">{currentProvider}</span>
          <span className="text-slate-500">/</span>
          <span className="font-mono text-[11px] text-slate-400 truncate max-w-[100px]">{currentModel}</span>
          <span
            className={`w-2 h-2 rounded-full ${
              isReady ? 'bg-emerald-500' : isDegraded ? 'bg-amber-500' : 'bg-rose-500'
            }`}
          />
        </button>

        {/* System Diagnostics Trigger */}
        <button
          onClick={onOpenDiagnostics}
          className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title="System Diagnostics & Knowledge Base Status"
        >
          <Activity className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
