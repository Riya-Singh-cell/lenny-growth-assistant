import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send,
  Sparkles,
  ExternalLink,
  Layers,
  ChevronDown,
  ChevronUp,
  FileText,
  Clock,
  User,
  AlertCircle
} from 'lucide-react';
import type { MessageItem, ArtifactPayload } from '../types';

interface ChatAreaProps {
  messages: MessageItem[];
  isLoading: boolean;
  onSendMessage: (text: string) => void;
  onOpenArtifact: (artifact: ArtifactPayload) => void;
  error: string | null;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onOpenArtifact,
  error,
}) => {
  const [inputText, setInputText] = useState('');
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    const text = inputText.trim();
    setInputText('');
    onSendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleSources = (msgId: string) => {
    setExpandedSources((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const suggestionPrompts = [
    {
      title: 'Prioritizing Growth Experiments',
      prompt: 'How should an early-stage startup prioritize growth experiments based on Lenny\'s guests?',
      category: 'Grounded Q&A'
    },
    {
      title: 'Adam Fishman on Onboarding',
      prompt: 'What did Adam Fishman explain about why onboarding is a 100% feature adoption lever?',
      category: 'Grounded Q&A'
    },
    {
      title: 'Ship 30 for 30 Essay',
      prompt: 'Write a Ship 30 for 30 style essay on product-led growth onboarding loops (~1,250 words).',
      category: 'Ship30 Skill'
    },
    {
      title: 'Visual HTML Growth Framework',
      prompt: 'Create a visual HTML version of a product retention and activation framework.',
      category: 'Artifact'
    }
  ];

  return (
    <main className="flex-1 flex flex-col h-full bg-slate-950 overflow-hidden relative">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 max-w-4xl w-full mx-auto space-y-6">
        {messages.length === 0 ? (
          /* Empty State */
          <div className="h-full flex flex-col items-center justify-center text-center py-12">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center mb-4 shadow-xl shadow-blue-500/20">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight mb-2">
              The Lenny Growth Assistant
            </h2>
            <p className="text-sm text-slate-400 max-w-md mb-8">
              Ask product and growth questions strictly grounded in Lenny's Podcast transcripts.
              Generate Ship 30 essays and standalone HTML/Markdown frameworks.
            </p>

            {/* Quick Starters Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl text-left">
              {suggestionPrompts.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(s.prompt)}
                  className="p-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 transition-all group text-left"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                      {s.title}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
                      {s.category}
                    </span>
                  </div>
                  <p className="text-[12px] text-slate-400 line-clamp-2">
                    {s.prompt}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Message Thread */
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            const sources = msg.sources || [];
            const hasSources = sources.length > 0;
            const areSourcesOpen = !!expandedSources[msg.id];

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} w-full`}
              >
                {/* Intent Badge for Assistant */}
                {!isUser && msg.intent && (
                  <div className="mb-1.5 flex items-center space-x-1.5 text-[11px] font-mono text-blue-400">
                    <span className="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20">
                      {msg.intent === 'SHIP30_ESSAY'
                        ? '✍️ Ship 30 for 30 Skill'
                        : msg.intent === 'ARTIFACT_GEN'
                        ? '🎨 Artifact Skill'
                        : '🎙️ Grounded Lenny Q&A'}
                    </span>
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`max-w-3xl rounded-2xl px-5 py-4 ${
                    isUser
                      ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-600/10'
                      : 'bg-slate-900 border border-slate-800/80 text-slate-100 rounded-bl-none shadow-sm'
                  }`}
                >
                  {isUser ? (
                    <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                  ) : (
                    <div className="prose-custom text-sm">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}

                  {/* Artifact Viewer Action Trigger */}
                  {msg.artifact && (
                    <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-xs text-slate-300">
                        <Layers className="w-4 h-4 text-indigo-400" />
                        <span className="font-semibold">{msg.artifact.title}</span>
                        <span className="uppercase text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                          {msg.artifact.type}
                        </span>
                      </div>
                      <button
                        onClick={() => onOpenArtifact(msg.artifact!)}
                        className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors shadow-sm shadow-indigo-500/20"
                      >
                        <span>Open in Artifact Viewer</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Source Citations Drawer */}
                {!isUser && hasSources && (
                  <div className="mt-2 w-full max-w-3xl">
                    <button
                      onClick={() => toggleSources(msg.id)}
                      className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors py-1 px-2 rounded-md hover:bg-slate-900/60"
                    >
                      <FileText className="w-3.5 h-3.5 text-blue-400" />
                      <span className="font-medium">
                        {sources.length} Lenny Podcast Transcript Source{sources.length > 1 ? 's' : ''}
                      </span>
                      {areSourcesOpen ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {areSourcesOpen && (
                      <div className="mt-2 p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2.5">
                        {sources.map((source, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/60 text-xs"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-1 mb-1.5">
                              <span className="font-semibold text-slate-200">
                                {source.episode}
                              </span>
                              {source.url && (
                                <a
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center space-x-1 text-blue-400 hover:text-blue-300 font-mono text-[11px]"
                                >
                                  <span>Watch on YouTube</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                            <div className="flex items-center space-x-3 text-[11px] text-slate-400 mb-1.5">
                              <span className="flex items-center space-x-1">
                                <User className="w-3 h-3 text-slate-500" />
                                <span>Speaker: {source.speaker || source.guest || 'Lenny'}</span>
                              </span>
                              {source.timestamp && (
                                <span className="flex items-center space-x-1">
                                  <Clock className="w-3 h-3 text-slate-500" />
                                  <span className="font-mono">{source.timestamp}</span>
                                </span>
                              )}
                            </div>
                            {source.snippet && (
                              <p className="text-[11px] text-slate-400 italic bg-slate-900/60 p-2 rounded border border-slate-800/40">
                                "{source.snippet}"
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center space-x-3 text-xs text-slate-400 bg-slate-900/80 border border-slate-800/80 px-4 py-3 rounded-2xl max-w-sm">
            <div className="w-4 h-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
            <span>Consulting Lenny's Podcast transcripts...</span>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="flex items-center space-x-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 px-4 py-3 rounded-xl max-w-2xl">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span className="flex-1">{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/60 backdrop-blur">
        <form
          onSubmit={handleSubmit}
          className="max-w-4xl mx-auto flex items-end space-x-2"
        >
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a growth question, request a Ship 30 essay, or generate an artifact..."
              rows={2}
              className="w-full resize-none rounded-xl bg-slate-900 border border-slate-800 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="h-11 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all shadow-sm shadow-blue-500/20"
            title="Send (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="max-w-4xl mx-auto mt-2 flex items-center justify-between text-[11px] text-slate-500 px-1">
          <span>Press <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">Enter</kbd> to submit, <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">Shift+Enter</kbd> for newline</span>
          <span>Lenny Transcript Grounded RAG</span>
        </div>
      </div>
    </main>
  );
};
