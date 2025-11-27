import Dexie, { Table } from "dexie";
import type { Conversation } from "@/lib/types/conversation";
import type { Message } from "@/lib/types/message";

export class ConversationDatabase extends Dexie {
  conversations!: Table<Conversation, string>;
  messages!: Table<Message, string>;

  constructor() {
    super("RecipeAgentDB");

    this.version(1).stores({
      conversations: "id, thread_id, created_at, updated_at",
      messages: "id, thread_id, timestamp",
    });
  }
}

export const db = new ConversationDatabase();
