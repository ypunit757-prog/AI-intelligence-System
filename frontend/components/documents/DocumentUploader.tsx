"use client";

import { useRef, useState } from "react";
import Button from "@/components/ui/Button";
import { api } from "@/lib/api";

export default function DocumentUploader({ onUploaded }: { onUploaded: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function upload(file: File) {
    setUploading(true);
    setError(null);
    try {
      await api.uploadDocument(file);
      onUploaded();
      setFileName(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed. Try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) upload(file);
      }}
      className={`rounded-card border border-dashed p-6 text-center transition-colors ${
        dragOver ? "border-accent bg-accent-muted" : "border-rule bg-white"
      }`}
    >
      <p className="font-serif text-sm text-ink">Drop a file here, or</p>
      <label className="mt-2 inline-block cursor-pointer text-sm font-medium text-accent hover:underline">
        browse your computer
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              setFileName(file.name);
              upload(file);
            }
          }}
        />
      </label>
      {uploading && <p className="mt-2 font-mono text-xs text-ink-muted">Uploading {fileName}…</p>}
      {error && <p className="mt-2 text-xs text-danger">{error}</p>}
      <div className="mt-4">
        <Button
          type="button"
          variant="secondary"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? "Uploading…" : "Choose file"}
        </Button>
      </div>
    </div>
  );
}
