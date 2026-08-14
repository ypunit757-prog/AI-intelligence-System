"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearToken, getToken } from "@/lib/auth";

const LINKS = [
  { href: "/chat", label: "Chat" },
  { href: "/documents", label: "Documents" },
  { href: "/search", label: "Search" },
];

export default function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(!!getToken());
  }, [pathname]);

  function handleLogout() {
    clearToken();
    setAuthed(false);
    router.push("/");
  }

  return (
    <header className="border-b border-rule bg-paper">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="font-serif text-lg font-semibold text-ink">Reading Room</span>
          <span className="hidden font-serif text-sm italic text-ink-muted sm:inline">
            answers, traced to their source
          </span>
        </Link>

        <nav className="flex items-center gap-6">
          {authed &&
            LINKS.map((link) => {
              const active = pathname?.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm ${
                    active ? "font-medium text-ink" : "text-ink-muted hover:text-ink"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}

          {authed ? (
            <div className="flex items-center gap-3 border-l border-rule pl-6">
              <Link href="/settings" className="text-sm text-ink-muted hover:text-ink">
                Settings
              </Link>
              <button
                onClick={handleLogout}
                className="rounded-full border border-rule px-3 py-1 text-xs text-ink-muted hover:border-ink hover:text-ink"
              >
                Log out
              </button>
            </div>
          ) : (
            <Link
              href="/"
              className="rounded-full bg-ink px-4 py-1.5 text-sm text-paper hover:bg-ink/90"
            >
              Sign in
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
