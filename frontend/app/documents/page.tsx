"use client";

import { useCallback, useEffect, useState } from "react";
import AuthGuard from "@/components/layout/AuthGuard";
import DocumentList from "@/components/documents/DocumentList";
import DocumentUploader from "@/components/documents/DocumentUploader";
import { DocumentItem, api } from "@/lib/api";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);

  const refresh = useCallback(() => {
    api.getDocuments().then(setDocuments).catch(() => setDocuments([]));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <AuthGuard>
      <div className="space-y-6">
        <div>
          <h1 className="font-serif text-2xl text-ink">Documents</h1>
          <p className="mt-1 text-sm text-ink-muted">
            What you upload here is the only thing Chat and Search are allowed to answer from.
          </p>
        </div>
        <DocumentUploader onUploaded={refresh} />
        <DocumentList documents={documents} onChanged={refresh} />
      </div>
    </AuthGuard>
  );
}
