"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { Message } from "@/lib/types/message";
import { sendCookingQuery, sendCookingQueryStream } from "@/lib/api/cooking";
import { conversationService } from "@/lib/services/conversationService";
import { db } from "@/lib/db/conversationDb";
import { useConversations } from "@/contexts/ConversationContext";

interface ThinkingStep {
  node: string;
  message: string;
  completed: boolean;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (query: string) => Promise<void>;
  clearError: () => void;
  resetConversation: () => void;
  threadId: string;
  thinkingSteps: ThinkingStep[];
}

/**
 * Custom hook for managing chat state and API interactions
 */
export function useChat(initialThreadId?: string): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const { refreshConversations } = useConversations();

  // Persist thread ID across requests
  const threadIdRef = useRef<string>(initialThreadId || crypto.randomUUID());

  // Load messages when thread ID changes
  useEffect(() => {
    if (initialThreadId) {
      threadIdRef.current = initialThreadId;
      loadMessages(initialThreadId);
    }
  }, [initialThreadId]);

  const loadMessages = async (threadId: string) => {
    try {
      // Try cache first for instant display
      const cached = await conversationService.getCachedMessages(threadId);
      if (cached.length > 0) {
        setMessages(cached);
      }

      // Fetch fresh data from server
      const { messages: freshMessages } = await conversationService.fetchConversation(threadId);
      setMessages(freshMessages);
    } catch (err) {
      console.error("Error loading messages:", err);
    }
  };

  const sendMessage = useCallback(
    async (query: string) => {
      const trimmedQuery = query.trim();
      if (!trimmedQuery) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmedQuery,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);
      setThinkingSteps([]);

      try {
        // Try streaming first
        await sendCookingQueryStream(
          trimmedQuery,
          threadIdRef.current,
          // onThinking callback
          (node, message) => {
            setThinkingSteps((prev) => {
              // Check if node already exists
              const existingIndex = prev.findIndex((s) => s.node === node);
              if (existingIndex >= 0) {
                // Mark as completed
                return prev.map((s, i) => (i === existingIndex ? { ...s, completed: true } : s));
              } else {
                // Add new step
                return [...prev, { node, message, completed: false }];
              }
            });
          },
          // onComplete callback
          (response, metadata) => {
            const assistantMessage: Message = {
              id: crypto.randomUUID(),
              role: "assistant",
              content: response,
              timestamp: new Date(),
              metadata,
            };

            setMessages((prev) => [...prev, assistantMessage]);
            db.messages.bulkPut([userMessage, assistantMessage]);
            setThinkingSteps([]);
            setIsLoading(false);

            // Refresh conversation list to show new/updated conversation
            refreshConversations();
          },
          // onError callback
          (errorMessage) => {
            setError(errorMessage);
            const errorMsg: Message = {
              id: crypto.randomUUID(),
              role: "error",
              content: errorMessage,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMsg]);
            setThinkingSteps([]);
            setIsLoading(false);
          }
        );
      } catch (err) {
        // Fallback to non-streaming API
        console.warn("Streaming failed, falling back to regular API:", err);
        try {
          const response = await sendCookingQuery(trimmedQuery, threadIdRef.current);
          const assistantMessage: Message = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: response.response,
            timestamp: new Date(),
            metadata: response.metadata,
          };
          setMessages((prev) => [...prev, assistantMessage]);
          await db.messages.bulkPut([userMessage, assistantMessage]);

          // Refresh conversation list to show new/updated conversation
          refreshConversations();
        } catch (fallbackErr) {
          const errorMessage =
            fallbackErr instanceof Error ? fallbackErr.message : "An error occurred";
          setError(errorMessage);
          const errorMsg: Message = {
            id: crypto.randomUUID(),
            role: "error",
            content: errorMessage,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMsg]);
        } finally {
          setIsLoading(false);
          setThinkingSteps([]);
        }
      }
    },
    [refreshConversations]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Reset conversation (new thread)
  const resetConversation = useCallback(() => {
    setMessages([]);
    threadIdRef.current = crypto.randomUUID();
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearError,
    resetConversation,
    threadId: threadIdRef.current,
    thinkingSteps,
  };
}
