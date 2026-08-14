"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { ChatSource, api } from "@/lib/api";

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  feedback?: 1 | -1;
}

export default function ChatWindow() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!input.trim()) {
      setError("Type a question first.");
      return;
    }
    setError(null);
    const question = input;
    setInput("");
    setTurns((t) => [...t, { role: "user", content: question }]);
    setLoading(true);
    try {
      const res = await api.chat(question, conversationId);
      setConversationId(res.conversation_id);
      setTurns((t) => [...t, { role: "assistant", content: res.answer, sources: res.sources }]);
    } catch (e) {
      setTurns((t) => [
        ...t,
        { role: "assistant", content: e instanceof Error ? e.message : "Something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleFeedback(index: number, rating: 1 | -1) {
    const turn = turns[index];
    const question = turns[index - 1]?.content ?? "";
    await api.feedback(question, turn.content, turn.sources ?? [], rating);
    setTurns((t) => t.map((x, i) => (i === index ? { ...x, feedback: rating } : x)));
  }

  return (
    <div className="flex flex-col">
      {turns.length === 0 && (
        <div className="rounded-card border border-dashed border-rule bg-white/50 px-6 py-10 text-center">
          <p className="font-serif text-lg text-ink">Nothing asked yet.</p>
          <p className="mt-1 text-sm text-ink-muted">
            Ask something about a document you&apos;ve uploaded — the answer will cite exactly
            where it came from.
          </p>
        </div>
      )}

      <div className="space-y-6">
        {turns.map((t, i) =>
          t.role === "user" ? (
            <div key={i} className="ml-auto max-w-[75%] rounded-2xl rounded-tr-sm bg-ink px-4 py-2.5 text-sm text-paper">
              {t.content}
            </div>
          ) : (
            <div key={i} className="max-w-[85%]">
              <p className="font-serif text-[17px] leading-relaxed text-ink">
                {t.content}
                {t.sources?.map((_, j) => (
                  <sup key={j} className="ml-0.5 font-mono text-[11px] font-medium text-accent">
                    [{j + 1}]
                  </sup>
                ))}
              </p>

              {t.sources && t.sources.length > 0 && (
                <div className="mt-3 space-y-2 rounded-card border border-rule bg-white p-3">
                  <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Sources</p>
                  {t.sources.map((s, j) => (
                    <div key={j} className="flex items-start gap-2 font-mono text-xs text-ink-muted">
                      <span className="mt-0.5 text-accent">[{j + 1}]</span>
                      <div className="flex-1">
                        <div className="mb-1 h-1 w-full overflow-hidden rounded-full bg-accent-muted">
                          <div
                            className="h-full bg-accent"
                            style={{ width: `${Math.round(Math.min(s.score, 1) * 100)}%` }}
                          />
                        </div>
                        <p className="line-clamp-2">{s.excerpt}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-2 flex gap-3">
                <button
                  onClick={() => handleFeedback(i, 1)}
                  className={`text-xs ${t.feedback === 1 ? "text-accent" : "text-ink-muted hover:text-ink"}`}
                >
                  Helpful
                </button>
                <button
                  onClick={() => handleFeedback(i, -1)}
                  className={`text-xs ${t.feedback === -1 ? "text-danger" : "text-ink-muted hover:text-ink"}`}
                >
                  Not helpful
                </button>
              </div>
            </div>
          )
        )}
        {loading && <p className="font-serif text-sm italic text-ink-muted">Reading your documents…</p>}
      </div>

      <div className="sticky bottom-6 mt-8 flex gap-2 rounded-full border border-rule bg-white p-1.5 shadow-sm">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about your documents"
          className="!border-none !bg-transparent !shadow-none focus:!shadow-none"
        />
        <Button onClick={handleSend} disabled={loading} className="shrink-0">
          {loading ? "…" : "Ask"}
        </Button>
      </div>
      {error && <p className="mt-2 text-xs text-danger">{error}</p>}
    </div>
  );
}
