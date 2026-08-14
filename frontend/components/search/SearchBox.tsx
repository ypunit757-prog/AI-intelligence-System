"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { SearchResultItem, api } from "@/lib/api";

export default function SearchBox() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch() {
    if (!query.trim()) {
      setError("Type something to search for first.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.search(query);
      setResults(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search the raw passages in your documents"
        />
        <Button onClick={handleSearch} disabled={loading} className="shrink-0">
          {loading ? "Searching…" : "Search"}
        </Button>
      </div>
      {error && <p className="text-xs text-danger">{error}</p>}

      {results !== null && results.length === 0 && (
        <p className="font-serif text-sm italic text-ink-muted">No matching passages found.</p>
      )}

      <div className="space-y-3">
        {results?.map((r) => (
          <div key={r.chunk_id} className="rounded-card border border-rule bg-white p-4">
            <div className="mb-2 h-1 w-full overflow-hidden rounded-full bg-accent-muted">
              <div
                className="h-full bg-accent"
                style={{ width: `${Math.round(Math.min(r.score, 1) * 100)}%` }}
              />
            </div>
            <p className="font-serif text-[15px] leading-relaxed text-ink">{r.content}</p>
            <p className="mt-2 font-mono text-[11px] text-ink-muted">
              relevance {r.score.toFixed(3)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
