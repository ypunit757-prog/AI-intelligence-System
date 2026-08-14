# AI Knowledge Intelligence Platform — Architecture

Status: **Planning phase only — no code has been written or verified.**
Any claim of "deployed", "tested", or "connected" below is explicitly marked NOT VERIFIED until proven.

---

## 1. Complete Architecture

```
                        USER
                          │
                          ▼
                  ┌───────────────┐
                  │    VERCEL     │   Next.js frontend
                  │   FRONTEND    │
                  └───────┬───────┘
                          │ HTTPS (JWT bearer)
                          ▼
                  ┌───────────────┐
                  │    RENDER     │   FastAPI backend
                  │   FASTAPI     │
                  └───────┬───────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
     PostgreSQL      Vector Store      LLM Provider
     (Render PG)     (pgvector /       (Ollama local /
                      FAISS/Chroma      Groq/OpenAI/
                      dev)              Gemini prod)
          │               │                │
          └───────┬───────┴────────────────┘
                  ▼
              AI ENGINE
                  │
      ┌───────────┼────────────┐
      ▼           ▼            ▼
     RAG        AGENT        TOOLS
```

Two independently deployable services (frontend on Vercel, backend on Render) communicating exclusively over HTTPS/JSON, with all AI logic, orchestration, and persistence isolated in the backend. No component is assumed permanent — every external dependency (LLM, storage, vector DB) is behind an interface so it can be swapped without touching business logic.

---

## 2. Vercel Architecture

- Hosts **only** the Next.js frontend (App Router, TypeScript, Tailwind).
- Build: `npm run build` on push; preview deployments per branch, production deployment on `main`.
- Environment variables scoped per Vercel environment (Development / Preview / Production): only `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_APP_ENV`.
- No server-side secrets, no database connections, no LLM calls originate from Vercel.
- Vercel's own serverless functions (`app/api/`) are reserved for thin proxy/BFF concerns only if needed later (e.g., setting httpOnly cookies) — not for AI logic.

## 3. Render Architecture

- Hosts the FastAPI backend as a native Python web service (Docker optional, not required).
- Reads `PORT` from Render's environment — never hardcoded.
- Startup sequence: install deps → run Alembic migrations → start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Render PostgreSQL add-on for the primary database (pgvector extension enabled).
- Stateless application container — nothing written to local disk is treated as durable; all persistent file data goes to object storage.
- `render.yaml` Blueprint defines the web service, environment variable placeholders, and (optionally) a managed Postgres instance.

## 4. Database Architecture

- **Engine:** PostgreSQL (Render-managed in production, local Postgres or Docker in dev).
- **ORM:** SQLAlchemy (async) + Alembic for migrations.
- **Vector extension:** pgvector, storing embedding vectors alongside chunk metadata for locality (single round trip for hybrid search).
- **Access pattern:** repository layer (`repositories/`) isolates SQLAlchemy from services; services never issue raw queries directly against sessions passed from routes.
- Read-only SQL path for the Database Agent, enforced by both a statement allow-list and a Postgres role with `SELECT`-only grants where possible.

## 5. Storage Architecture

- `StorageInterface` (abstract): `upload`, `download`, `delete`, `exists`.
- `LocalStorage`: writes to a local dev folder — used only in local development, never assumed durable on Render.
- `S3CompatibleStorage`: implements the interface against any S3-compatible provider (e.g., Cloudflare R2, Backblaze B2, AWS S3), configured entirely via environment variables (`STORAGE_PROVIDER`, `STORAGE_BUCKET`, `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`).
- Selection is runtime-configured (`STORAGE_PROVIDER=local|s3`), never hardcoded per environment in code.

## 6. RAG Architecture

```
Query → Classification → Rewriting → Retriever → Hybrid Search
      → Reranker → Context Compression → Prompt Construction
      → LLM → Citation Verification → Answer → Frontend
```

- **Retriever:** dense (embeddings) + sparse (keyword/BM25-style) combined into hybrid search, with metadata filtering and a similarity threshold.
- **Reranker:** optional cross-encoder pass (`RERANKER_MODEL`) over top-N hybrid results before compression.
- **Context compression:** trims retrieved chunks to what fits the prompt budget, prioritized by rerank score.
- **Citation verification:** post-generation check that cited chunk IDs actually appear in the retrieved context before returning to the frontend.

## 7. Agent Architecture

```
User → Intent → Planner → Tool Selection → Tool Execution
     → Observation → Validation → Final Answer
```

Built on LangGraph as a explicit state graph (not a free-form loop), with:
- `max_iterations`, per-tool timeout, max tool calls, and max total execution time enforced at the graph level.
- Tools: Calculator, Document Search, Semantic Search, Database Query (read-only), CSV Analysis, Python Analysis (sandboxed), Web Search, Code Analysis.
- No tool may invoke arbitrary shell commands; each tool has a strict input schema validated before execution.

## 8. Frontend Architecture

- Next.js App Router with route groups: `chat/`, `documents/`, `search/`, `settings/`.
- All network I/O routed through `lib/api.ts` — no component issues raw `fetch` calls directly.
- Streaming chat rendered via SSE consumption in a dedicated hook (`hooks/useChatStream.ts`).
- Component structure mirrors domain: `components/chat`, `components/documents`, `components/search`, `components/ui` (shared primitives), `components/layout`.

## 9. Backend Architecture

- FastAPI + Pydantic (schemas) + SQLAlchemy (models/repositories) + Alembic (migrations).
- Layering: `api/routes` (HTTP only) → `services` (business logic) → `repositories` (data access) → `database` (session/engine).
- `ai/` subtree isolates embeddings, LLM providers, RAG pipeline, retrieval, reranking, agents, and prompt templates behind interfaces so providers are swappable via config alone.
- `security/` centralizes JWT handling, password hashing, and authorization checks reused across routes.

## 10. API Specification

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Root/info |
| GET | `/health` | Liveness — always returns `{"status": "ok"}` |
| GET | `/ready` | Readiness — checks DB, vector store, critical deps |
| POST | `/documents/upload` | Upload a document |
| GET | `/documents` | List user's documents |
| GET | `/documents/{id}` | Document detail |
| DELETE | `/documents/{id}` | Delete a document |
| POST | `/documents/{id}/reindex` | Re-run processing/embedding |
| POST | `/search` | Semantic/hybrid search |
| POST | `/chat` | Chat (RAG), streaming via SSE |
| POST | `/agent` | Agent invocation |
| GET | `/conversations` | List conversations |
| GET | `/conversations/{id}` | Conversation detail + messages |
| DELETE | `/conversations/{id}` | Delete conversation |
| POST | `/feedback` | Submit 👍/👎 feedback |
| GET | `/metrics` | Operational metrics |

All routes except `/`, `/health`, `/ready` require a valid JWT and enforce per-user ownership.

## 11. Database Schema (high level)

- **users**: id, email, hashed_password, created_at
- **documents**: id, user_id (FK), filename, storage_key, status, mime_type, size, created_at
- **document_chunks**: id, document_id (FK), content, metadata (jsonb), embedding (vector), chunk_index
- **conversations**: id, user_id (FK), title, created_at
- **messages**: id, conversation_id (FK), role, content, created_at
- **tool_calls**: id, message_id (FK), tool_name, input, output, latency_ms, status
- **search_logs**: id, user_id (FK), query, top_k, latency_ms, created_at
- **feedback**: id, user_id (FK), message_id (FK), question, answer, sources, rating, created_at
- **evaluation_results**: id, run_id, metric_name, value, created_at

All user-owned tables carry `user_id` and every query is scoped by the authenticated user — enforced in the repository layer, not just at the route.

## 12. Environment Variable Plan

**Backend:** `APP_ENV`, `DATABASE_URL`, `VECTOR_STORE`, `LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `SIMILARITY_THRESHOLD`, `RERANKER_MODEL`, `CORS_ORIGINS`, `JWT_SECRET`, `STORAGE_PROVIDER`, `STORAGE_BUCKET`, `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`

**Frontend:** `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_ENV`

Rule: nothing secret ever gets a `NEXT_PUBLIC_` prefix; `.env` files are never committed (see §26 Git Security below).

## 13. Free/Local Tool List (Development)

Python, FastAPI, Next.js, PostgreSQL (local/Docker), FAISS/Chroma, Sentence Transformers, Hugging Face models, Ollama, Redis (local/Docker), LangChain, LangGraph, Docker, pytest, Ruff, Black, MyPy, GitHub Actions (free tier for public/small private repos).

## 14. Production Tool List

Vercel (frontend hosting, free tier), Render (backend + Postgres, free/starter tier), pgvector, an S3-compatible object storage provider (e.g., Cloudflare R2 free tier), a hosted LLM provider selected via `LLM_PROVIDER` (Groq/OpenAI/Gemini — paid, optional), Redis (optional, for cache — paid tier on Render if used in production).

## 15. Folder Structure

```
ai-knowledge-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/ (health, documents, search, chat, agents, feedback)
│   │   ├── api/dependencies.py
│   │   ├── config/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── database/
│   │   ├── security/
│   │   ├── monitoring/
│   │   ├── ai/ (embeddings, llm, rag, retrieval, reranking, agents, prompts)
│   │   ├── tools/
│   │   ├── storage/
│   │   └── utils/
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/ (page.tsx, chat/, documents/, search/, settings/, api/)
│   ├── components/ (chat/, documents/, search/, ui/, layout/)
│   ├── lib/ (api.ts, auth.ts, config.ts)
│   ├── hooks/, types/, public/
│   ├── package.json
│   └── .env.example
├── evaluation/ (dataset.json, evaluate_retrieval.py, evaluate_rag.py, results/)
├── docker-compose.yml
├── render.yaml
├── README.md
├── .gitignore
└── .github/workflows/ci.yml
```

## 16. Development Phases

1. Repo scaffold + config classes (`Settings`/`DevelopmentSettings`/`ProductionSettings`) + Docker Compose (local Postgres/Redis)
2. Auth (JWT, password hashing, protected routes) + users table
3. Storage abstraction (`LocalStorage` first) + document upload/list/delete endpoints
4. Document processing pipeline (extract → clean → chunk → metadata)
5. Embedding interface + FAISS/Chroma dev vector store
6. Basic RAG pipeline (retrieve → prompt → LLM via Ollama) + `/chat`
7. Hybrid search + reranker + citation verification
8. Agent (LangGraph) + tool set + safety limits
9. Conversation memory + token-aware history truncation
10. Frontend: dashboard, upload UI, chat UI, streaming
11. Feedback loop + evaluation harness
12. Observability (structured logging, request IDs) + caching
13. Swap dev vector store for pgvector; swap `LocalStorage` for `S3CompatibleStorage`
14. CI/CD (GitHub Actions: lint, type-check, test, build)

## 17. Deployment Phases

1. Provision Render Postgres, enable `pgvector`
2. Deploy backend to Render via `render.yaml`, verify `/health` and `/ready`
3. Configure backend env vars (DB, storage, LLM provider) on Render
4. Provision S3-compatible bucket, wire `STORAGE_*` vars
5. Deploy frontend to Vercel, set `NEXT_PUBLIC_API_URL` to the Render URL
6. Set `CORS_ORIGINS` on the backend to the Vercel production domain
7. Smoke-test end-to-end (upload → search → chat) against production URLs
8. Enable CI/CD gating on `main`

## 18. Security Architecture

- JWT-based auth, hashed passwords, per-user authorization enforced in repositories (not just routes).
- Strict CORS via `CORS_ORIGINS` env var — never `allow_origins=["*"]` in production.
- Input validation (Pydantic schemas), file size/type/MIME validation, path traversal protection on storage keys.
- Parameterized queries throughout (SQLAlchemy) — no raw string SQL interpolation.
- Prompt injection defense: document content wrapped in explicit `<document_context>` delimiters and never treated as instructions; system/tool policies are immutable regardless of document content.
- Tool sandboxing: no shell execution, strict schemas, timeouts, iteration caps.
- Rate limiting at the API layer (per-user/per-IP).
- Centralized, sanitized error responses — no stack traces leaked in production.

## 19. Evaluation Architecture

- `evaluation/dataset.json`: curated query/expected-answer/expected-source sets.
- `evaluate_retrieval.py`: Recall@K, Precision@K, MRR, Hit Rate.
- `evaluate_rag.py`: Faithfulness, Answer Relevance, Context Relevance, Citation Accuracy, end-to-end Latency, Error Rate.
- Results written to `evaluation/results/` with timestamped runs feeding the `evaluation_results` table for trend tracking.

## 20. CI/CD Architecture

GitHub Actions, on every push:
1. Install backend + frontend dependencies
2. Backend: Ruff → Black `--check` → MyPy → pytest
3. Frontend: `npm run lint` → `npm run build`
4. (Backend build is implicitly validated by successful dependency install + test run; no separate build artifact required for a Python service)

Failing any step blocks merge; nothing here claims deployment success — that's verified separately per §17.

## 21. Cost Optimization Strategy

- Default to free tiers everywhere: Vercel (frontend), Render (backend + small Postgres), Ollama for local LLM inference, an S3-compatible free-tier bucket (e.g., R2) for storage.
- Hosted LLM provider is opt-in and configurable — the app runs on Ollama at zero marginal cost during development.
- Redis is optional; in-memory caching is the free-tier default, Redis reserved for when scale justifies the paid add-on.
- Document limitations explicitly rather than assume permanence: free Render services sleep on inactivity and have limited CPU/RAM; free Postgres tiers cap storage; free object storage tiers cap bandwidth/requests.

## 22. Local Development Strategy

- `docker-compose.yml` brings up Postgres, Redis, backend, and (optionally) frontend for local parity.
- Vector store defaults to FAISS/Chroma locally to avoid requiring pgvector setup during early iteration.
- LLM defaults to Ollama (`LLM_PROVIDER=ollama`) so no API key is required to develop.
- `.env.example` files document every variable without real secrets.

## 23. Vercel Deployment Strategy

- Connect the GitHub repo, set root directory to `frontend/`.
- Configure `NEXT_PUBLIC_API_URL` per environment (Preview → a staging Render URL if available, Production → the production Render URL).
- No server secrets stored in Vercel; the frontend is a pure client of the Render API.

## 24. Render Deployment Strategy

- `render.yaml` Blueprint defines the web service (`backend/`), build command, start command (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`), and health check path (`/health`).
- Database provisioned as a Render Postgres instance; `DATABASE_URL` injected automatically via Blueprint linkage where supported.
- Migrations run as part of the deploy step before the server starts accepting traffic.

## 25. Risks and Limitations

- Free-tier Render services sleep after inactivity, causing cold-start latency on the first request.
- Free Postgres tiers have storage and connection limits that will require a paid upgrade at scale.
- CPU-only embedding/reranking on Render (no assumed GPU) limits throughput for large document batches.
- Local LLM (Ollama) quality/speed differs materially from hosted providers — dev/prod behavior parity is not guaranteed and must be evaluated, not assumed.
- pgvector performance at large chunk counts depends on proper indexing (e.g., IVFFlat/HNSW) not yet designed in detail — to be addressed when the schema is implemented.
- Prompt injection defenses reduce but do not eliminate risk from malicious document content; ongoing evaluation is required.
- Nothing in this document has been executed — all local/Vercel/Render/database/test claims are **NOT VERIFIED** until actually run.

---

**STOP.** This is the complete architecture per the requested scope. No code has been generated. Waiting for **NEXT** to begin Iteration 1 (repo scaffold + config classes) of the looping development process.
