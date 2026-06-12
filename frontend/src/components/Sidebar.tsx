import { useRef } from 'react';
import type { Session } from '../types';

interface SidebarProps {
  sessions: Session[];
  activeSessionHash: string | null;
  isLoading: boolean;
  onSessionSelect: (session: Session) => void;
  onUpload: (file: File) => void;
  onNewChat: () => void;
  onDeleteSession: (hash: string) => void;
}

export default function Sidebar({
  sessions,
  activeSessionHash,
  isLoading,
  onSessionSelect,
  onUpload,
  onNewChat,
  onDeleteSession,
}: SidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
          <span>binaryRE</span>
        </div>
        <p className="sidebar-subtitle">二进制分析控制台</p>
      </div>

      <div className="sidebar-actions">
        <button
          className="sidebar-btn sidebar-btn-primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <span>{isLoading ? '上传中...' : '上传二进制文件'}</span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="sidebar-file-input"
          onChange={handleFileChange}
          accept="*/*"
        />
        <button className="sidebar-btn sidebar-btn-secondary" onClick={onNewChat}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          <span>新对话</span>
        </button>
      </div>

      <div className="session-list">
        {sessions.length === 0 ? (
          <div className="session-list-empty">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8"
                 strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            <p>暂无会话</p>
            <p className="hint">上传二进制文件开始</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.full_hash}
              className={`session-item ${session.full_hash === activeSessionHash ? 'active' : ''}`}
              onClick={() => onSessionSelect(session)}
            >
              <div className="session-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div className="session-info">
                <span className="session-name" title={session.binary}>
                  {session.binary.length > 24
                    ? session.binary.slice(0, 22) + '...'
                    : session.binary}
                </span>
                <span className="session-meta">
                  #{session.hash} · {session.time}
                </span>
              </div>
              <button
                className="session-delete-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.full_hash);
                }}
                title="删除会话"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <span>binaryRE v0.1</span>
        <span className="dot">·</span>
        <span>Kali + Ghidra + r2</span>
      </div>
    </aside>
  );
}
