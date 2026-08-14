"use client";

import { useCallback, useState } from "react";
import { API_URL } from "@/lib/config";
import { getToken } from "@/lib/auth";

export function useChatStream() {
  const [streaming, setStreaming] = useState(false);
  const [partial, setPartial] = useState("");

  const send = useCallback(async (message: string, onDone: (full: string) => void) => {
    setStreaming(true);
    setPartial("");
    let full = "";

    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken() ?? ""}`,
      },
      body: JSON.stringify({ message, stream: true }),
    });

    const reader = res.body?.getReader();
    const decoder = new TextDecoder();
    if (!reader) {
      setStreaming(false);
      return;
    }

    // Minimal SSE parsing: split on double-newline event boundaries.
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunkText = decoder.decode(value, { stream: true });
      for (const line of chunkText.split("\n")) {
        if (line.startsWith("data: ")) {
          const delta = line.slice(6);
          full += delta;
          setPartial(full);
        }
      }
    }

    setStreaming(false);
    onDone(full);
  }, []);

  return { send, streaming, partial };
}
