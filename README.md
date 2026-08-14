# AI Knowledge Intelligence Platform

A RAG + agent knowledge platform: Next.js frontend on Vercel, FastAPI backend
on Render, PostgreSQL + pgvector for storage and retrieval.

> **Status:** This is a first, functionally complete iteration generated in
> one pass. Nothing below has been executed in this environment — treat every
> "should work" as **NOT VERIFIED** until you've run it yourself locally.

## 1. Project Overview

- **Frontend (`frontend/`)** — Next.js 14 App Router, TypeScript, Tailwind.
  Dashboard, document upload/list, semantic search, streaming chat, settings/auth.
- **Backend (`backend/`)** — FastAPI. Auth (JWT), document ingestion pipeline,
  hybrid RAG pipeline, LangGraph agent with tool-use, feedback loop.
- **Database** — PostgreSQL, pgvector for embeddings in production; FAISS for
  local development.
- **Storage** — pluggable `StorageInterface` (Local for dev, S3-compatible for prod).
- **LLM** — pluggable `LLMInterface` (Ollama for dev, OpenAI/Groq/Gemini for prod).

## 2. Architecture

See `architecture.md` (generated in the planning phase) for the full diagrammed
architecture, API spec, schema, and phased rollout plan.

## 3. Local Installation

Prerequisites: Python 3.11+, Node 20+, Docker (optional but recommended), Ollama (optional).

```bash
git clone <this-repo>
cd ai-knowledge-intelligence
```

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000/health

### Option B — Run natively

```bash
# Postgres (with pgvector) via Docker, everything else native
docker run -d --name pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=aiknowledge -p 5432:5432 pgvector/pgvector:pg16

cd backend
cp .env.example .env   # edit as needed
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## 4. Environment Variables

See `backend/.env.example` and `frontend/.env.example` for the full list.
Never commit real `.env` files — see Security below.

## 5. PostgreSQL Setup

Local: use the `postgres` service in `docker-compose.yml` (image
`pgvector/pgvector:pg16`, which ships the extension pre-installed).
Production: Render-managed Postgres (see `render.yaml`).

## 6. pgvector Setup

The extension is enabled by the first Alembic migration
(`CREATE EXTENSION IF NOT EXISTS vector`). No manual step needed beyond
running migrations against a Postgres instance that supports the extension
(the `pgvector/pgvector` image and Render's Postgres both do).

## 7. Ollama Setup (local LLM)

```bash
# Install from https://ollama.com, then:
ollama pull llama3
ollama serve
```

`OLLAMA_BASE_URL` defaults to `http://localhost:11434`. Set `LLM_PROVIDER=ollama`.

## 8. Model Setup (embeddings)

The default embedding model (`sentence-transformers/all-MiniLM-L6-v2`) downloads
automatically on first use via Hugging Face. No API key required.

## 9. Running the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

## 10. Running the Frontend

```bash
cd frontend
npm run dev
```

## 11. Running Tests

```bash
cd backend
pytest
```

> Tests that hit a real database expect `DATABASE_URL` to point at a running
> Postgres instance. Storage/chunking/security unit tests run with no
> external dependencies.

## 12. Docker

`docker-compose.yml` runs `frontend`, `backend`, `postgres`, and `redis`
together for local parity with production topology. Docker is **not**
required for either Vercel or Render deployment.

## 13. GitHub Actions

`.github/workflows/ci.yml` runs lint/type-check/test for the backend and
lint/build for the frontend on every push and PR to `main`.

## 14. Render Deployment

1. Push this repo to GitHub.
2. In Render, "New +" → "Blueprint" → point at this repo (`render.yaml` is auto-detected).
3. Fill in the `sync: false` secrets in the Render dashboard (`GROQ_API_KEY`,
   `STORAGE_BUCKET`, `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`).
4. Update `CORS_ORIGINS` to your real Vercel domain once you have it.
5. Deploy. Verify `https://<your-backend>.onrender.com/health` returns `{"status": "ok"}`.

**NOT VERIFIED** — confirm this deploy succeeds before relying on it.

## 15. Vercel Deployment

1. Import this repo into Vercel, set the project root to `frontend/`.
2. Set `NEXT_PUBLIC_API_URL` to your Render backend URL.
3. Deploy.

**NOT VERIFIED** — confirm this deploy succeeds before relying on it.

## 16. Database Migration

```bash
cd backend
alembic revision -m "describe your change"   # create a new migration
alembic upgrade head                          # apply migrations
```

Never edit the production schema by hand.

## 17. Storage Configuration

Set `STORAGE_PROVIDER=local` for development (files land in `LOCAL_STORAGE_DIR`).
Set `STORAGE_PROVIDER=s3` for production and fill in `STORAGE_BUCKET`,
`STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY` for any
S3-compatible provider (AWS S3, Cloudflare R2, Backblaze B2, MinIO, ...).

## 18. Production Configuration

Driven entirely by environment variables — see `app/config/settings.py`.
No `if production:` branches in business logic; behavior differs only
through which values are injected.

## 19. Troubleshooting

- **`/ready` reports database error** — check `DATABASE_URL` and that
  migrations have run (`alembic upgrade head`).
- **Embeddings very slow** — confirm device detection picked CPU as
  expected on Render (no GPU available there by default); consider a
  smaller embedding model if latency is unacceptable.
- **CORS errors in the browser** — `CORS_ORIGINS` on the backend must
  exactly match your frontend's origin (scheme + host, no trailing slash).
- **Render cold starts** — free-tier services sleep after inactivity;
  the first request after idle will be slow. This is expected, not a bug.

## 20. Security

- JWT auth, bcrypt password hashing, per-user data isolation enforced in
  repositories.
- Strict CORS via env var, never `*` in production.
- File type/size/MIME validation on upload; path-traversal-safe storage keys.
- SQL injection prevented via SQLAlchemy parameterization everywhere.
- Agent's database tool only runs pre-validated `SELECT` statements;
  `DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE` are blocked.
- Document content is treated as untrusted data (`<document_context>`
  delimiters) and can never override system/tool policy.
- No secrets committed — see `.gitignore`; never use `NEXT_PUBLIC_` for
  anything secret.

## 21. Evaluation

```bash
cd evaluation
python evaluate_retrieval.py --dataset dataset.json
python evaluate_rag.py --dataset dataset.json
```

Extend `dataset.json` with real query/expected-keyword cases from your own
documents. Results are written to `evaluation/results/`.

---

## Known Limitations (read before deploying)

- Free Render/Vercel/Postgres tiers have sleep, CPU, RAM, storage, and
  bandwidth limits — no tier here is "permanently free" at scale.
- The agent's planner is a lightweight heuristic, not full LLM function-calling —
  adequate for a first version, but replace with structured tool-calling for
  more reliable tool selection.
- Gemini streaming currently falls back to non-streaming internally
  (see `app/ai/llm/gemini_provider.py`) — swap in true SSE parsing if you need it.
- Hybrid (keyword + vector) search is not yet implemented — current retrieval
  is vector-only; add a keyword/BM25 pass in `app/ai/retrieval/` as a follow-up.
- No rate limiting middleware is wired in yet — add one (e.g. `slowapi`) before
  exposing this publicly.
