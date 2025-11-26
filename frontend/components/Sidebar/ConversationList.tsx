"use client";

import { useConversations } from "@/contexts/ConversationContext";
import { ConversationItem } from "./ConversationItem";

export function ConversationList() {
  const { conversations, isLoading } = useConversations();

  if (isLoading) {
    return <div className="p-4 text-gray-400 text-sm">Loading conversations...</div>;
  }

  if (conversations.length === 0) {
    return (
      <div className="p-4 text-gray-400 text-sm text-center">
        No conversations yet.
        <br />
        Start a new one!
      </div>
    );
  }

  return (
    <div className="py-2">
      {conversations.map((conversation) => (
        <ConversationItem key={conversation.id} conversation={conversation} />
      ))}
    </div>
  );
}
