"use client";

import Button from "@/components/ui/Button";
import { DocumentItem, api } from "@/lib/api";

const STATUS_STYLE: Record<string, string> = {
  indexed: "bg-accent-muted text-accent",
  processing: "bg-amber-50 text-amber-700",
  uploaded: "bg-amber-50 text-amber-700",
  failed: "bg-danger-muted text-danger",
};

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentList({
  documents,
  onChanged,
}: {
  documents: DocumentItem[];
  onChanged: () => void;
}) {
  async function handleDelete(id: string) {
    await api.deleteDocument(id);
    onChanged();
  }

  async function handleReindex(id: string) {
    await api.reindexDocument(id);
    onChanged();
  }

  if (documents.length === 0) {
    return (
      <div className="rounded-card border border-dashed border-rule px-6 py-10 text-center">
        <p className="font-serif text-sm text-ink-muted">No documents yet. Upload one above to get started.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-card border border-rule bg-white">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-rule font-mono text-[11px] uppercase tracking-wider text-ink-muted">
            <th className="px-4 py-3 font-medium">File</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Size</th>
            <th className="px-4 py-3 font-medium"></th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id} className="border-b border-rule last:border-0">
              <td className="px-4 py-3 font-medium text-ink">{doc.filename}</td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-0.5 font-mono text-[11px] ${STATUS_STYLE[doc.status] || "bg-paper text-ink-muted"}`}>
                  {doc.status}
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-ink-muted">{formatSize(doc.size)}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => handleReindex(doc.id)} className="!px-2 !py-1 text-xs">
                    Reindex
                  </Button>
                  <Button variant="ghost" onClick={() => handleDelete(doc.id)} className="!px-2 !py-1 text-xs text-danger hover:text-danger">
                    Delete
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
