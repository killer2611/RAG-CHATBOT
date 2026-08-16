import type { Metadata } from "next";
import { ChatContainer } from "@/components/chat/chat-container";

export const metadata: Metadata = {
  title: "Chat Workspace",
  description:
    "Ask your indexed knowledge base with real-time hierarchical retrieval and grounded evidence.",
};

export default function ChatPage() {
  return <ChatContainer />;
}
