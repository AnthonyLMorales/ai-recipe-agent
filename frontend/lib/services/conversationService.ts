import { db } from "@/lib/db/conversationDb";
import type { Conversation } from "@/lib/types/conversation";
import type { Message } from "@/lib/types/message";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const conversationService = {
  // Fetch all conversations from server and cache in IndexedDB
  async fetchConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE_URL}/api/conversations`);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to fetch conversations: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    const data = await response.json();
    const conversations = data.conversations.map((conv: Record<string, unknown>) => ({
      ...conv,
      created_at: new Date(conv.created_at as string),
      updated_at: new Date(conv.updated_at as string),
    }));

    // Cache in IndexedDB
    await db.conversations.bulkPut(conversations);

    return conversations;
  },

  // Fetch a specific conversation with messages
  async fetchConversation(
    threadId: string
  ): Promise<{ conversation: Conversation; messages: Message[] }> {
    const response = await fetch(`${API_BASE_URL}/api/conversations/${threadId}`);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to fetch conversation: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    const data = await response.json();

    const conversation = {
      ...data.conversation,
      created_at: new Date(data.conversation.created_at),
      updated_at: new Date(data.conversation.updated_at),
    };

    const messages = data.messages.map((msg: Record<string, unknown>) => ({
      ...msg,
      timestamp: new Date(msg.timestamp as string),
    }));

    // Cache in IndexedDB
    await db.conversations.put(conversation);
    await db.messages.bulkPut(messages);

    return { conversation, messages };
  },

  // Create new conversation
  async createConversation(title?: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/api/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: title || null }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to create conversation: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    const conversation = await response.json();
    const conv = {
      ...conversation,
      created_at: new Date(conversation.created_at),
      updated_at: new Date(conversation.updated_at),
    };

    await db.conversations.put(conv);

    return conv;
  },

  // Delete conversation
  async deleteConversation(threadId: string): Promise<void> {
    await fetch(`${API_BASE_URL}/api/conversations/${threadId}`, {
      method: "DELETE",
    });

    // Remove from IndexedDB
    await db.conversations.where("thread_id").equals(threadId).delete();
    await db.messages.where("thread_id").equals(threadId).delete();
  },

  // Update conversation title
  async updateConversationTitle(threadId: string, title: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/api/conversations/${threadId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to update conversation: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    const conversation = await response.json();
    const conv = {
      ...conversation,
      created_at: new Date(conversation.created_at),
      updated_at: new Date(conversation.updated_at),
    };

    await db.conversations.put(conv);

    return conv;
  },

  // Get conversations from cache
  async getCachedConversations(): Promise<Conversation[]> {
    return await db.conversations.orderBy("updated_at").reverse().toArray();
  },

  // Get messages from cache
  async getCachedMessages(threadId: string): Promise<Message[]> {
    return await db.messages.where("thread_id").equals(threadId).sortBy("timestamp");
  },
};
