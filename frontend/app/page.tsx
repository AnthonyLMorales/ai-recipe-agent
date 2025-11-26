import { ChatContainer } from "@/components/Chat/ChatContainer";
import { ConversationProvider } from "@/contexts/ConversationContext";

export default function Home() {
  return (
    <ConversationProvider>
      <ChatContainer />
    </ConversationProvider>
  );
}
