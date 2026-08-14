"""Token-aware conversation history truncation.

Never send unlimited history to the LLM — keep the most recent
messages that fit inside a token budget (approximate, via tiktoken).
"""
from typing import List

import tiktoken

from app.ai.llm.interface import ChatMessage

_ENCODING = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


def truncate_history(messages: List[ChatMessage], max_tokens: int = 3000) -> List[ChatMessage]:
    total = 0
    kept: List[ChatMessage] = []
    for msg in reversed(messages):
        t = _count_tokens(msg["content"])
        if total + t > max_tokens:
            break
        kept.append(msg)
        total += t
    return list(reversed(kept))
