"use client";

import { useState } from "react";
import type { Conversation } from "@/lib/types/conversation";
import { useConversations } from "@/contexts/ConversationContext";
import { formatDistanceToNow } from "date-fns";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConversationItemProps {
  conversation: Conversation;
}

export function ConversationItem({ conversation }: ConversationItemProps) {
  const { currentConversation, setCurrentConversation, deleteConversation } = useConversations();
  const [showMenu, setShowMenu] = useState(false);

  const isActive = currentConversation?.id === conversation.id;

  const handleClick = () => {
    setCurrentConversation(conversation);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("Delete this conversation?")) {
      await deleteConversation(conversation.thread_id);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={cn(
        "px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors relative",
        isActive && "bg-gray-800 border-l-2 border-primary"
      )}
      onMouseEnter={() => setShowMenu(true)}
      onMouseLeave={() => setShowMenu(false)}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">
            {conversation.title || "Untitled Conversation"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {formatDistanceToNow(new Date(conversation.updated_at), { addSuffix: true })}
          </p>
        </div>

        {showMenu && (
          <Button
            onClick={handleDelete}
            variant="ghost"
            size="icon"
            className="ml-2 h-8 w-8"
            aria-label="Delete conversation"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
