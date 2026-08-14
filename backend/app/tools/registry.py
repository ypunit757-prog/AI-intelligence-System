"""Agent tools with strict input validation, timeouts, and no shell
access. Each tool is a small async function with a Pydantic input
schema — the agent graph is responsible for enforcing max_iterations
and total execution time (see app/ai/agents/graph.py)."""
import asyncio
import json
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import text as sql_text

TOOL_TIMEOUT_SECONDS = 15

BLOCKED_SQL_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE"}


class CalculatorInput(BaseModel):
    expression: str = Field(..., max_length=200)


async def calculator_tool(input: CalculatorInput) -> dict:
    import math

    allowed = {"__builtins__": {}, "math": math, "abs": abs, "round": round, "min": min, "max": max}
    try:
        result = eval(input.expression, allowed, {})  # noqa: S307 — restricted namespace, numeric only
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


class DocumentSearchInput(BaseModel):
    query: str = Field(..., max_length=500)
    top_k: int = Field(5, ge=1, le=20)


async def document_search_tool(input: DocumentSearchInput, user_id: str) -> dict:
    from app.ai.embeddings.sentence_transformer_embeddings import get_embedding_model
    from app.ai.retrieval.factory import get_vector_store

    embedder = get_embedding_model()
    store = get_vector_store()
    query_embedding = embedder.embed_query(input.query)
    results = await store.similarity_search(query_embedding, top_k=input.top_k, user_id=user_id)
    return {"results": results}


class DatabaseQueryInput(BaseModel):
    question: str = Field(..., max_length=500)


def _is_safe_readonly_sql(sql: str) -> bool:
    upper = sql.strip().upper()
    if not upper.startswith("SELECT"):
        return False
    return not any(kw in upper for kw in BLOCKED_SQL_KEYWORDS)


async def database_query_tool(input: DatabaseQueryInput, generated_sql: str, session) -> dict:
    """Executes only pre-validated, LLM-generated READ-ONLY SQL.
    generated_sql must be produced upstream (see agent graph) and is
    re-validated here as defense in depth."""
    if not _is_safe_readonly_sql(generated_sql):
        return {"error": "Only read-only SELECT statements are permitted."}
    try:
        result = await asyncio.wait_for(session.execute(sql_text(generated_sql)), timeout=TOOL_TIMEOUT_SECONDS)
        rows = [dict(r._mapping) for r in result.fetchall()]
        return {"rows": rows}
    except asyncio.TimeoutError:
        return {"error": "Query timed out."}
    except Exception as e:
        return {"error": str(e)}


class CsvAnalysisInput(BaseModel):
    csv_text: str
    question: str = Field(..., max_length=500)


async def csv_analysis_tool(input: CsvAnalysisInput) -> dict:
    import io

    import pandas as pd  # local import — optional dependency, only needed for this tool

    try:
        df = pd.read_csv(io.StringIO(input.csv_text))
        summary = {
            "columns": list(df.columns),
            "row_count": len(df),
            "describe": json.loads(df.describe(include="all").to_json()),
        }
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}


TOOL_REGISTRY: dict[str, Any] = {
    "calculator": calculator_tool,
    "document_search": document_search_tool,
    "database_query": database_query_tool,
    "csv_analysis": csv_analysis_tool,
}
