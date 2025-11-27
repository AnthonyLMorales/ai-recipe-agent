export interface Conversation {
  id: string;
  thread_id: string;
  title: string | null;
  created_at: Date;
  updated_at: Date;
  message_count: number;
  last_message?: Message;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface ConversationDetailResponse {
  conversation: Conversation;
  messages: Message[];
}

// Re-export Message type from message.ts
import type { Message } from "./message";
export type { Message };
