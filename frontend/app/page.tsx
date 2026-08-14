"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import { api } from "@/lib/api";
import { getToken, saveToken } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (getToken()) {
      router.replace("/chat");
    } else {
      setChecking(false);
    }
  }, [router]);

  async function handleSubmit() {
    if (!email.trim() || !password.trim()) {
      setError("Enter an email and password first.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const res = mode === "login" ? await api.login(email, password) : await api.register(email, password);
      saveToken(res.access_token);
      router.replace("/chat");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (checking) return null;

  return (
    <div className="grid gap-12 py-8 md:grid-cols-2 md:items-center">
      <div>
        <p className="mb-3 font-mono text-xs uppercase tracking-wider text-ink-muted">
          Retrieval-augmented · agentic
        </p>
        <h1 className="font-serif text-4xl leading-tight text-ink">
          Ask your documents.
          <br />
          Every answer, traced to its source.
        </h1>
        <p className="mt-4 max-w-md text-ink-muted">
          Upload what you know. Reading Room answers only from what you&apos;ve given it, and
          shows the exact passage behind every claim, numbered like a footnote.
        </p>
      </div>

      <Card className="max-w-sm justify-self-end">
        <div className="mb-4 flex gap-1 rounded-full bg-paper p-1">
          <button
            onClick={() => setMode("login")}
            className={`flex-1 rounded-full py-1.5 text-sm ${
              mode === "login" ? "bg-white font-medium text-ink shadow-sm" : "text-ink-muted"
            }`}
          >
            Sign in
          </button>
          <button
            onClick={() => setMode("register")}
            className={`flex-1 rounded-full py-1.5 text-sm ${
              mode === "register" ? "bg-white font-medium text-ink shadow-sm" : "text-ink-muted"
            }`}
          >
            Create account
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs text-ink-muted">Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-ink-muted">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              placeholder="At least 8 characters"
            />
          </div>
          {error && <p className="text-xs text-danger">{error}</p>}
          <Button onClick={handleSubmit} disabled={submitting} className="w-full justify-center">
            {submitting ? "One moment…" : mode === "login" ? "Sign in" : "Create account"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
