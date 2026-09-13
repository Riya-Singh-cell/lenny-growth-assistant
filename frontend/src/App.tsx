import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ArtifactViewer } from './components/ArtifactViewer';
import { DiagnosticsModal } from './components/DiagnosticsModal';
import type {
  SessionSummary,
  SessionDetail,
  MessageItem,
  ArtifactPayload,
  ReadinessResponse
} from './types';
import * as api from './services/api';

export const App: React.FC = () => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
  const [activeArtifact, setActiveArtifact] = useState<ArtifactPayload | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [currentProvider, setCurrentProvider] = useState<string>('ollama');
  const [currentModel, setCurrentModel] = useState<string>('llama3.2');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load readiness status
  const loadReadiness = useCallback(async () => {
    try {
      const data = await api.fetchReadiness();
      setReadiness(data);
      if (data.llm_provider) {
        setCurrentProvider(data.llm_provider.provider);
        setCurrentModel(data.llm_provider.model);
      }
    } catch (err: any) {
      console.warn('Backend readiness check error:', err);
    }
  }, []);

  // Load session list
  const loadSessions = useCallback(async () => {
    try {
      const list = await api.listSessions();
      setSessions(list);
      if (list.length > 0 && !activeSessionId) {
        setActiveSessionId(list[0].id);
      } else if (list.length === 0) {
        // Auto-create initial session
        const newSess = await api.createSession('New Conversation');
        setSessions([newSess]);
        setActiveSessionId(newSess.id);
      }
    } catch (err: any) {
      console.error('Failed to load sessions:', err);
      setError('Could not connect to backend server. Make sure the FastAPI backend is running on port 8000.');
    }
  }, [activeSessionId]);

  // Load active session details
  useEffect(() => {
    if (!activeSessionId) {
      setActiveSession(null);
      return;
    }
    api.getSession(activeSessionId)
      .then((detail) => {
        setActiveSession(detail);
        setError(null);
        // If session has artifacts and none selected, open latest artifact
        if (detail.artifacts && detail.artifacts.length > 0 && !activeArtifact) {
          api.getArtifact(detail.artifacts[0].id).then(setActiveArtifact).catch(() => {});
        }
      })
      .catch((err: any) => {
        console.error('Failed to fetch session detail:', err);
        setError(`Failed to load conversation: ${err.message}`);
      });
  }, [activeSessionId]);

  useEffect(() => {
    loadReadiness();
    loadSessions();
  }, [loadReadiness, loadSessions]);

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
    setActiveArtifact(null);
    setError(null);
  };

  const handleNewSession = async () => {
    try {
      const newSession = await api.createSession('New Conversation');
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setActiveArtifact(null);
      setError(null);
    } catch (err: any) {
      setError(`Failed to create new conversation: ${err.message}`);
    }
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteSession(id);
      const remaining = sessions.filter((s) => s.id !== id);
      setSessions(remaining);
      if (activeSessionId === id) {
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
        } else {
          handleNewSession();
        }
      }
    } catch (err: any) {
      setError(`Failed to delete conversation: ${err.message}`);
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!activeSessionId) return;

    setError(null);
    setIsLoading(true);

    // Optimistic UI message
    const tempUserMsg: MessageItem = {
      id: `temp-${Date.now()}`,
      session_id: activeSessionId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString()
    };

    setActiveSession((prev) => prev ? {
      ...prev,
      messages: [...prev.messages, tempUserMsg]
    } : null);

    try {
      const res = await api.sendMessage({
        session_id: activeSessionId,
        message: text,
        provider: currentProvider,
        model: currentModel
      });

      const assistantMsg: MessageItem = {
        id: res.message_id,
        session_id: res.session_id,
        role: 'assistant',
        content: res.content,
        intent: res.intent,
        sources: res.sources,
        created_at: new Date().toISOString(),
        artifact: res.artifact
      };

      setActiveSession((prev) => prev ? {
        ...prev,
        messages: prev.messages.filter((m) => m.id !== tempUserMsg.id).concat([tempUserMsg, assistantMsg]),
        artifacts: res.artifact ? [res.artifact, ...(prev.artifacts || [])] : (prev.artifacts || [])
      } : null);

      // Auto-open artifact if one was created
      if (res.artifact) {
        setActiveArtifact(res.artifact);
      }

      // Update session title in sidebar if updated
      setSessions((prev) =>
        prev.map((s) => (s.id === activeSessionId && s.title === 'New Conversation' ? { ...s, title: text.slice(0, 40) + '...' } : s))
      );

    } catch (err: any) {
      console.error('Chat error:', err);
      setError(
        err.message ||
        'Error communicating with AI model. Please verify Ollama is running or check model settings in the header.'
      );
      // Remove optimistic message if failure
      setActiveSession((prev) => prev ? {
        ...prev,
        messages: prev.messages.filter((m) => m.id !== tempUserMsg.id)
      } : null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectProvider = (provider: string, model: string) => {
    setCurrentProvider(provider);
    setCurrentModel(model);
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Header */}
      <Header
        readiness={readiness}
        currentProvider={currentProvider}
        currentModel={currentModel}
        onSelectProvider={handleSelectProvider}
        onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
      />

      {/* Main Split Layout: Sidebar + Chat + Artifact Viewer */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
          chunkCount={readiness?.vector_store?.total_chunks || 0}
        />

        {/* Center Main Chat */}
        <ChatArea
          messages={activeSession?.messages || []}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
          onOpenArtifact={setActiveArtifact}
          error={error}
        />

        {/* Right Artifact Panel */}
        {activeArtifact && (
          <ArtifactViewer
            artifact={activeArtifact}
            onClose={() => setActiveArtifact(null)}
          />
        )}
      </div>

      {/* Diagnostics / Settings Modal */}
      <DiagnosticsModal
        isOpen={isDiagnosticsOpen}
        onClose={() => setIsDiagnosticsOpen(false)}
        readiness={readiness}
        onRefresh={loadReadiness}
        currentProvider={currentProvider}
        currentModel={currentModel}
        onSelectProvider={handleSelectProvider}
      />
    </div>
  );
};

export default App;
