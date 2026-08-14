"use client";

import { useEffect, useState } from "react";
import AuthGuard from "@/components/layout/AuthGuard";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [status, setStatus] = useState("checking…");

  useEffect(() => {
    api
      .health()
      .then((r) => setStatus(r.status))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <AuthGuard>
      <div className="mx-auto max-w-md space-y-4">
        <h1 className="font-serif text-2xl text-ink">Settings</h1>
        <Card>
          <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Backend status</p>
          <p className="mt-1 font-serif text-lg text-ink">{status}</p>
        </Card>
        <Card>
          <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Account</p>
          <p className="mt-1 text-sm text-ink-muted">
            Signed in. Use the &quot;Log out&quot; button in the top navigation to switch accounts.
          </p>
        </Card>
      </div>
    </AuthGuard>
  );
}
