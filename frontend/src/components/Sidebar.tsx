import React from 'react';
import { Plus, MessageSquare, Trash2, BookOpen } from 'lucide-react';
import type { SessionSummary } from '../types';

interface SidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  chunkCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  chunkCount,
}) => {
  return (
    <aside className="w-64 h-full bg-slate-900 border-r border-slate-800 flex flex-col select-none shrink-0">
      {/* New Chat Button */}
      <div className="p-3 border-b border-slate-800/80">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-all shadow-sm shadow-blue-500/20 active:scale-[0.98]"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Session History Header */}
      <div className="px-3 pt-3 pb-1 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
        Conversations ({sessions.length})
      </div>

      {/* Session History List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {sessions.length === 0 ? (
          <div className="py-8 px-3 text-center text-xs text-slate-500">
            No conversations yet.
            <br />
            Start a new session above!
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`group flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                  isActive
                    ? 'bg-slate-800 text-white font-medium border border-slate-700/60'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-2 truncate pr-2">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                  <span className="truncate">{session.title || 'Untitled Session'}</span>
                </div>
                <button
                  onClick={(e) => onDeleteSession(session.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 rounded transition-opacity"
                  title="Delete Conversation"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Bottom Knowledge Base Indicator */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/50 text-[11px] text-slate-400">
        <div className="flex items-center space-x-2 text-slate-300 font-medium mb-1">
          <BookOpen className="w-3.5 h-3.5 text-blue-400" />
          <span>Lenny Transcript Base</span>
        </div>
        <div className="flex items-center justify-between text-[10px] text-slate-400">
          <span>Total Chunks Indexed</span>
          <span className="font-mono text-blue-400 bg-blue-500/10 px-1.5 py-0.2 rounded border border-blue-500/20 font-semibold">
            {chunkCount}
          </span>
        </div>
      </div>
    </aside>
  );
};
