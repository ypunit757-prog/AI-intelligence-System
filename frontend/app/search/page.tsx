import AuthGuard from "@/components/layout/AuthGuard";
import SearchBox from "@/components/search/SearchBox";

export default function SearchPage() {
  return (
    <AuthGuard>
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-1 font-serif text-2xl text-ink">Search</h1>
        <p className="mb-6 text-sm text-ink-muted">
          The raw passages behind Chat&apos;s answers, ranked by relevance.
        </p>
        <SearchBox />
      </div>
    </AuthGuard>
  );
}
