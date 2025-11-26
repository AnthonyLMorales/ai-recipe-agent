import type { Message as MessageType } from "@/lib/types/message";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MessageProps {
  message: MessageType;
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === "user";
  const isError = message.role === "error";

  // Format timestamp
  const timeString = message.timestamp.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className="flex flex-col gap-1 max-w-[80%] md:max-w-[70%]">
        <Card
          className={cn(
            "p-3 whitespace-pre-wrap wrap-break-word bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-white dark:text-gray-100",
            isUser && "bg-primary text-primary-foreground border-primary",
            isError && "bg-destructive/10 border-destructive text-destructive"
          )}
        >
          {message.content}
        </Card>
        <span className={cn("text-xs text-muted-foreground", isUser ? "text-right" : "text-left")}>
          {timeString}
        </span>
      </div>
    </div>
  );
}
