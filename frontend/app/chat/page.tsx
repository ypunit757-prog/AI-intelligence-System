import AuthGuard from "@/components/layout/AuthGuard";
import ChatWindow from "@/components/chat/ChatWindow";

export default function ChatPage() {
  return (
    <AuthGuard>
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 font-serif text-2xl text-ink">Chat</h1>
        <ChatWindow />
      </div>
    </AuthGuard>
  );
}
