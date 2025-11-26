"use client";

import { useEffect, useRef } from "react";
import type { Message as MessageType } from "@/lib/types/message";
import { Message } from "./Message";
import { ThinkingSteps } from "./ThinkingSteps";

interface ThinkingStep {
  node: string;
  message: string;
  completed: boolean;
}

interface MessageListProps {
  messages: MessageType[];
  isLoading: boolean;
  thinkingSteps?: ThinkingStep[];
}

export function MessageList({ messages, isLoading, thinkingSteps = [] }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 bg-gray-100 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto w-full space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400 text-center">
            <p className="text-lg">
              Start a conversation by asking about recipes, cooking techniques, or ingredients!
            </p>
          </div>
        )}

        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[80%]">
              <ThinkingSteps steps={thinkingSteps} />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
