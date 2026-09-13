export interface SourceCitation {
  chunk_id?: string;
  episode: string;
  guest?: string;
  speaker: string;
  timestamp: string;
  url?: string;
  relevance_score?: number;
  snippet?: string;
}

export interface ArtifactPayload {
  id: string;
  session_id: string;
  title: string;
  type: 'markdown' | 'html';
  content: string;
  sanitized_content?: string;
  created_at?: string;
}

export interface MessageItem {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  intent?: 'GROUNDED_QA' | 'SHIP30_ESSAY' | 'ARTIFACT_GEN';
  created_at: string;
  artifact?: ArtifactPayload;
}

export interface SessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  user_metadata?: Record<string, any>;
}

export interface SessionDetail extends SessionSummary {
  messages: MessageItem[];
  artifacts: ArtifactPayload[];
}

export interface LLMProviderStatus {
  provider: string;
  model: string;
  is_available: boolean;
  error?: string;
  available_models: string[];
}

export interface ReadinessResponse {
  status: 'ready' | 'degraded' | 'not_ready';
  database: string;
  llm_provider: LLMProviderStatus;
  vector_store: {
    total_chunks: number;
    is_populated: boolean;
    store_path: string;
  };
}
