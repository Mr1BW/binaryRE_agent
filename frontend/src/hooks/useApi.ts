import { useRef, useCallback, useState } from 'react';
import type { ChatMessage, Session } from '../types';

const API_BASE = '/api';

export function useApi() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: Session[] = await res.json();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }, []);

  const uploadBinary = useCallback(
    async (file: File): Promise<{ success: boolean; sessionHash?: string }> => {
      setIsUploading(true);
      try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(`${API_BASE}/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error((errData as { detail?: string }).detail || '上传失败');
        }

        const data = (await res.json()) as {
          success: boolean;
          session_hash: string;
          binary_name: string;
        };

        await loadSessions();
        return { success: true, sessionHash: data.session_hash };
      } catch (err) {
        console.error('Upload failed:', err);
        return { success: false };
      } finally {
        setIsUploading(false);
      }
    },
    [loadSessions]
  );

  const sendMessage = useCallback(
    async function* (
      message: string,
      history: ChatMessage[],
      sessionHash: string
    ): AsyncGenerator<{ history: ChatMessage[]; done?: boolean; error?: string }> {
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      try {
        const res = await fetch(`${API_BASE}/chat/${sessionHash}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, history }),
          signal: abortRef.current.signal,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error((errData as { detail?: string }).detail || '请求失败');
        }

        const reader = res.body?.getReader();
        if (!reader) throw new Error('无法读取响应流');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6));
                if (event.history) {
                  yield {
                    history: event.history as ChatMessage[],
                    done: event.type === 'done',
                  };
                }
                if (event.error) {
                  yield { history, error: event.error };
                  return;
                }
              } catch {
                continue;
              }
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          throw err;
        }
      }
    },
    []
  );

  const cancelMessage = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const loadSessionHistory = useCallback(
    async (sessionHash: string): Promise<ChatMessage[]> => {
      try {
        const res = await fetch(`${API_BASE}/sessions/${sessionHash}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { history: ChatMessage[] };
        return data.history || [];
      } catch (err) {
        console.error('Failed to load session history:', err);
        return [];
      }
    },
    []
  );

  const deleteSession = useCallback(
    async (sessionHash: string): Promise<boolean> => {
      try {
        const res = await fetch(`${API_BASE}/sessions/${sessionHash}`, {
          method: 'DELETE',
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        await loadSessions();
        return true;
      } catch (err) {
        console.error('Delete session failed:', err);
        return false;
      }
    },
    [loadSessions]
  );

  return {
    sessions,
    isUploading,
    loadSessions,
    uploadBinary,
    sendMessage,
    cancelMessage,
    deleteSession,
    loadSessionHistory,
  };
}
