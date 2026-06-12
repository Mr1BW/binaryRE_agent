import { useState, useEffect, useCallback } from 'react';
import type { ChatMessage, Session } from './types';
import { useApi } from './hooks/useApi';
import Sidebar from './components/Sidebar';
import Welcome from './components/Welcome';
import ChatArea from './components/ChatArea';
import './App.css';

export default function App() {
  const api = useApi();
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [activeSessionHash, setActiveSessionHash] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.loadSessions();
  }, []);

  const handleUpload = useCallback(
    async (file: File) => {
      setError(null);
      const result = await api.uploadBinary(file);

      if (result.success && result.sessionHash) {
        setActiveSession(null);
        setActiveSessionHash(result.sessionHash);
        setError(null);

        const history = await api.loadSessionHistory(result.sessionHash);
        setMessages(history);
      } else {
        setError('上传二进制文件失败。后端是否正在运行？');
      }
    },
    [api]
  );

  const handleSessionSelect = useCallback(
    async (session: Session) => {
      setActiveSession(session);
      setActiveSessionHash(session.full_hash);
      setError(null);

      const history = await api.loadSessionHistory(session.full_hash);
      setMessages(history);
    },
    [api]
  );

  const handleNewChat = useCallback(() => {
    setActiveSession(null);
    setActiveSessionHash(null);
    setMessages([]);
    setError(null);
  }, []);

  const handleDeleteSession = useCallback(
    async (hash: string) => {
      await api.deleteSession(hash);
      if (activeSession?.full_hash === hash) {
        handleNewChat();
      }
    },
    [api, activeSession, handleNewChat]
  );

  const handleSend = useCallback(
    async (message: string) => {
      if (!activeSessionHash) {
        setError('请先上传一个二进制文件。');
        return;
      }

      setError(null);
      setIsStreaming(true);

      const userMsg: ChatMessage = { role: 'user', content: message };
      const updatedHistory = [...messages, userMsg];
      setMessages(updatedHistory);

      try {
        const generator = api.sendMessage(message, messages, activeSessionHash);

        for await (const chunk of generator) {
          if (chunk.error) {
            setError(chunk.error);
            break;
          }
          if (chunk.history) {
            setMessages(chunk.history);
          }
          if (chunk.done) break;
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setError(`错误: ${(err as Error).message}`);
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [messages, activeSessionHash, api]
  );

  const handleCancel = useCallback(() => {
    api.cancelMessage();
    setIsStreaming(false);
  }, [api]);

  return (
    <div className="app-layout">
      <Sidebar
        sessions={api.sessions}
        activeSessionHash={activeSession?.full_hash ?? activeSessionHash}
        isLoading={api.isUploading}
        onSessionSelect={handleSessionSelect}
        onUpload={handleUpload}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
      />

      <main className="main-content">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        )}

        {!activeSession && messages.length === 0 && !activeSessionHash ? (
          <Welcome onUploadClick={() => {}} />
        ) : (
          <ChatArea
            messages={messages}
            isStreaming={isStreaming}
            onSend={handleSend}
            onCancel={handleCancel}
          />
        )}
      </main>
    </div>
  );
}
