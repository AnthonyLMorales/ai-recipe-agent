// Frontend message types for chat display

export type MessageRole = "user" | "assistant" | "error";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: {
    query_type?: string;
    is_relevant?: boolean;
    dish?: string;
  };
}
