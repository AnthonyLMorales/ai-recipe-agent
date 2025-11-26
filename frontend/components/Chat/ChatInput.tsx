"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSend: (query: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900 p-4">
      <div className="max-w-4xl mx-auto flex gap-2">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about recipes, cooking techniques, or ingredients..."
          disabled={disabled}
          className="flex-1 resize-none max-h-32 overflow-y-auto bg-white! dark:bg-gray-800! text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
          rows={1}
        />
        <Button onClick={handleSend} disabled={disabled || !input.trim()} size="lg">
          <Send className="h-4 w-4" />
          Send
        </Button>
      </div>
    </div>
  );
}
