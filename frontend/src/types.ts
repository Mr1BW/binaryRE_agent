export interface Session {
  hash: string;
  full_hash: string;
  binary: string;
  binary_path: string;
  time: string;
  has_state: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;
  metadata?: {
    title?: string;
    id?: string;
    parent_id?: string;
  };
}

export interface GradioState {
  messages: unknown[];
  binary_path?: string;
  session_path?: string;
  disassembled_path?: string;
}
