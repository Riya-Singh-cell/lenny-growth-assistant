import type {
  SessionSummary,
  SessionDetail,
  ArtifactPayload,
  ReadinessResponse
} from '../types';

const API_BASE = '';

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const res = await fetch(`${API_BASE}/ready`);
  if (!res.ok) {
    throw new Error(`Readiness check failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function listSessions(): Promise<SessionSummary[]> {
  const res = await fetch(`${API_BASE}/api/sessions`);
  if (!res.ok) {
    throw new Error(`Failed to list sessions (HTTP ${res.status})`);
  }
  return res.json();
}

export async function createSession(title?: string): Promise<SessionSummary> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: title || 'New Conversation' })
  });
  if (!res.ok) {
    throw new Error(`Failed to create session (HTTP ${res.status})`);
  }
  return res.json();
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  if (!res.ok) {
    throw new Error(`Failed to get session details (HTTP ${res.status})`);
  }
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    throw new Error(`Failed to delete session (HTTP ${res.status})`);
  }
}

export interface SendMessagePayload {
  session_id: string;
  message: string;
  provider?: string;
  model?: string;
}

export interface SendMessageResponse {
  message_id: string;
  session_id: string;
  role: string;
  content: string;
  intent: 'GROUNDED_QA' | 'SHIP30_ESSAY' | 'ARTIFACT_GEN';
  sources: any[];
  artifact?: ArtifactPayload;
  provider: string;
  model: string;
}

export async function sendMessage(payload: SendMessagePayload): Promise<SendMessageResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Chat request failed (HTTP ${res.status})`);
  }
  return res.json();
}

export async function getArtifact(artifactId: string): Promise<ArtifactPayload> {
  const res = await fetch(`${API_BASE}/api/artifacts/${artifactId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch artifact (HTTP ${res.status})`);
  }
  return res.json();
}
