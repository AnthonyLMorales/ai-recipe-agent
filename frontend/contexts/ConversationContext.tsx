"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import type { Conversation } from "@/lib/types/conversation";
import { conversationService } from "@/lib/services/conversationService";

interface ConversationContextType {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  setCurrentConversation: (conversation: Conversation | null) => void;
  createNewConversation: () => Promise<Conversation>;
  deleteConversation: (threadId: string) => Promise<void>;
  refreshConversations: () => Promise<void>;
}

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      // Try cache first for instant display
      const cached = await conversationService.getCachedConversations();
      if (cached.length > 0) {
        setConversations(cached);
      }

      // Fetch fresh data from server
      const fresh = await conversationService.fetchConversations();
      setConversations(fresh);
    } catch (error) {
      console.error("Error loading conversations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const createNewConversation = async () => {
    const conversation = await conversationService.createConversation();
    setConversations((prev) => [conversation, ...prev]);
    setCurrentConversation(conversation);
    return conversation;
  };

  const deleteConversation = async (threadId: string) => {
    await conversationService.deleteConversation(threadId);
    setConversations((prev) => prev.filter((c) => c.thread_id !== threadId));
    if (currentConversation?.thread_id === threadId) {
      setCurrentConversation(null);
    }
  };

  const refreshConversations = async () => {
    await loadConversations();
  };

  return (
    <ConversationContext.Provider
      value={{
        conversations,
        currentConversation,
        isLoading,
        setCurrentConversation,
        createNewConversation,
        deleteConversation,
        refreshConversations,
      }}
    >
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversations() {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error("useConversations must be used within ConversationProvider");
  }
  return context;
}
