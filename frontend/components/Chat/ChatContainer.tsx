"use client";

import { useChat } from "@/hooks/useChat";
import { useConversations } from "@/contexts/ConversationContext";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { ErrorMessage } from "../ui/ErrorMessage";
import { Sidebar } from "../Sidebar/Sidebar";

export function ChatContainer() {
  const { currentConversation } = useConversations();
  const { messages, isLoading, error, sendMessage, clearError, resetConversation, thinkingSteps } =
    useChat(currentConversation?.thread_id);

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {currentConversation?.title || "Recipe Agent"}
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Your AI cooking assistant powered by LangGraph
              </p>
            </div>

            {/* Reset button (only show if messages exist) */}
            {messages.length > 0 && (
              <button
                onClick={resetConversation}
                className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-md transition-colors"
                aria-label="Start new conversation"
              >
                New Conversation
              </button>
            )}
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="px-4 pt-4">
            <div className="max-w-4xl mx-auto">
              <ErrorMessage message={error} onDismiss={clearError} />
            </div>
          </div>
        )}

        {/* Messages */}
        <MessageList messages={messages} isLoading={isLoading} thinkingSteps={thinkingSteps} />

        {/* Input */}
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}
