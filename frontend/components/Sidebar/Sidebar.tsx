"use client";

import { useState } from "react";
import { ConversationList } from "./ConversationList";
import { useConversations } from "@/contexts/ConversationContext";

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { createNewConversation } = useConversations();

  return (
    <div
      className={`bg-gray-900 text-white transition-all duration-300 ${
        isCollapsed ? "w-0" : "w-64"
      } flex flex-col border-r border-gray-700 relative`}
    >
      {!isCollapsed && (
        <>
          {/* Header */}
          <div className="p-4 border-b border-gray-700">
            <button
              onClick={createNewConversation}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white rounded-lg px-4 py-2 flex items-center justify-center gap-2 transition-colors"
            >
              <span className="text-lg">+</span>
              New Conversation
            </button>
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto">
            <ConversationList />
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700 text-xs text-gray-400">Recipe Agent</div>
        </>
      )}

      {/* Toggle Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute top-4 -right-3 bg-gray-800 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-gray-700 z-10"
      >
        {isCollapsed ? "→" : "←"}
      </button>
    </div>
  );
}
