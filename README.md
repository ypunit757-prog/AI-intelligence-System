# AI Knowledge Intelligence Platform

A Retrieval-Augmented Generation (RAG) + agent knowledge platform that lets you upload documents (PDFs and more) and ask questions about their contents. Built with a **Next.js** frontend, a **FastAPI** backend, and **PostgreSQL + pgvector** for storage and vector retrieval.

> **Status:** First functionally complete iteration, generated in one pass. Nothing below has been executed in this environment yet — treat every "should work" as **NOT VERIFIED** until you've run it yourself locally.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Local Installation](#3-local-installation)
4. [Environment Variables](#4-environment-variables)
5. [PostgreSQL Setup](#5-postgresql-setup)
6. [pgvector Setup](#6-pgvector-setup)
7. [Ollama Setup (local LLM)](#7-ollama-setup-local-llm)
8. [Model Setup (embeddings)](#8-model-setup-embeddings)
9. [Running the Backend](#9-running-the-backend)
10. [Running the Frontend](#10-running-the-frontend)
11. [Running Tests](#11-running-tests)
12. [Docker](#12-docker)
13. [GitHub Actions (CI)](#13-github-actions)
14. [Render Deployment](#14-render-deployment)
15. [Vercel Deployment](#15-vercel-deployment)
16. [Database Migrations](#16-database-migrations)
17. [Storage Configuration](#17-storage-configuration)
18. [Production Configuration](#18-production-configuration)
19. [API Reference](#19-api-reference)
20. [Troubleshooting](#20-troubleshooting)
21. [Security](#21-security)
22. [Evaluation](#22-evaluation)
23. [Known Limitations](#23-known-limitations-read-before-deploying)

---

## 1. Project Overview

- **Frontend (`frontend/`)** — Next.js 14 (App Router), TypeScript, Tailwind CSS. Provides a dashboard, document upload/list, semantic search, streaming chat, and settings/auth screens.
- **Backend (`backend/`)** — FastAPI service handling JWT auth, the document ingestion pipeline, a hybrid RAG pipeline, and a LangGraph-based agent with tool use and a feedback loop.
- **Database** — PostgreSQL with the `pgvector` extension for embedding storage in production; FAISS/Chroma for local development.
- **Storage** — Pluggable `StorageInterface` (local filesystem for dev, S3-compatible object storage for prod — AWS S3, Cloudflare R2, Backblaze B2, MinIO, etc.).
- **LLM** — Pluggable `LLMInterface` (Ollama for local/free development, OpenAI / Groq / Gemini for production).

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

Two independently deployable services (frontend on Vercel, backend on Render) communicate exclusively over HTTPS/JSON. All AI logic, orchestration, and persistence live in the backend. Every external dependency (LLM, storage, vector DB) sits behind an interface so it can be swapped without touching business logic.

## 2. Architecture

See [`architecture.md`](./architecture.md) for the full diagrammed architecture, database schema, API spec, and phased build/deploy plan — including the RAG pipeline (query rewriting → hybrid retrieval → reranking → context compression → citation verification) and the LangGraph agent design (planner → tool selection → execution → validation).

## 3. Local Installation

**Prerequisites:** Python 3.11+, Node 20+, Docker (optional but recommended), Ollama (optional, for local LLM inference).

```bash
git clone https://github.com/ypunit757-prog/AI-intelligence-System.git
cd AI-intelligence-System
```

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000/health

### Option B — Run natively

```bash
# Postgres (with pgvector) via Docker; everything else runs natively
docker run -d --name pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=aiknowledge \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

```bash
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

See `backend/.env.example` and `frontend/.env.example` for the full list of variables. **Never commit real `.env` files** — see [Security](#21-security).

Key backend variables: `APP_ENV`, `DATABASE_URL`, `VECTOR_STORE`, `LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `SIMILARITY_THRESHOLD`, `RERANKER_MODEL`, `CORS_ORIGINS`, `JWT_SECRET`, `STORAGE_PROVIDER`, `STORAGE_BUCKET`, `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`.

Key frontend variables: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_ENV`.

## 5. PostgreSQL Setup

- **Local:** use the `postgres` service in `docker-compose.yml` (image `pgvector/pgvector:pg16`, which ships the extension pre-installed).
- **Production:** Render-managed Postgres (see `render.yaml`).

## 6. pgvector Setup

The extension is enabled by the first Alembic migration (`CREATE EXTENSION IF NOT EXISTS vector`). No manual step is needed beyond running migrations against a Postgres instance that supports the extension (the `pgvector/pgvector` image and Render's Postgres both do).

## 7. Ollama Setup (local LLM)

```bash
# Install from https://ollama.com, then:
ollama pull llama3
ollama serve
```

`OLLAMA_BASE_URL` defaults to `http://localhost:11434`. Set `LLM_PROVIDER=ollama` to use it.

## 8. Model Setup (embeddings)

The default embedding model (`sentence-transformers/all-MiniLM-L6-v2`) downloads automatically on first use via Hugging Face. No API key required.

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

Tests that hit a real database expect `DATABASE_URL` to point at a running Postgres instance. Storage/chunking/security unit tests run with no external dependencies.

## 12. Docker

`docker-compose.yml` runs `frontend`, `backend`, `postgres`, and `redis` together for local parity with the production topology. Docker is **not** required for either Vercel or Render deployment.

## 13. GitHub Actions

`.github/workflows/ci.yml` runs lint/type-check/test for the backend and lint/build for the frontend on every push and PR to `main`.

## 14. Render Deployment

1. Push this repo to GitHub.
2. In Render: **New +** → **Blueprint** → point at this repo (`render.yaml` is auto-detected).
3. Fill in the `sync: false` secrets in the Render dashboard: `GROQ_API_KEY`, `STORAGE_BUCKET`, `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`.
4. Update `CORS_ORIGINS` to your real Vercel domain once you have it.
5. Deploy, then verify `https://<your-backend>.onrender.com/health` returns `{"status": "ok"}`.

**NOT VERIFIED** — confirm this deploy succeeds before relying on it.

## 15. Vercel Deployment

1. Import this repo into Vercel; set the project root to `frontend/`.
2. Set `NEXT_PUBLIC_API_URL` to your Render backend URL.
3. Deploy.

**NOT VERIFIED** — confirm this deploy succeeds before relying on it.

## 16. Database Migrations

```bash
cd backend
alembic revision -m "describe your change"   # create a new migration
alembic upgrade head                          # apply migrations
```

Never edit the production schema by hand.

## 17. Storage Configuration

- `STORAGE_PROVIDER=local` for development — files land in `LOCAL_STORAGE_DIR`.
- `STORAGE_PROVIDER=s3` for production — fill in `STORAGE_BUCKET`, `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY` for any S3-compatible provider (AWS S3, Cloudflare R2, Backblaze B2, MinIO, ...).

## 18. Production Configuration

Driven entirely by environment variables — see `app/config/settings.py`. There are no `if production:` branches in business logic; behavior differs only through which values are injected.

## 19. API Reference

| Method | Path                       | Purpose                                             |
| ------ | -------------------------- | ---------------------------------------------------- |
| GET    | `/`                         | Root/info                                            |
| GET    | `/health`                   | Liveness — always returns `{"status": "ok"}`         |
| GET    | `/ready`                    | Readiness — checks DB, vector store, critical deps   |
| POST   | `/documents/upload`         | Upload a document                                    |
| GET    | `/documents`                | List user's documents                                |
| GET    | `/documents/{id}`           | Document detail                                      |
| DELETE | `/documents/{id}`           | Delete a document                                    |
| POST   | `/documents/{id}/reindex`   | Re-run processing/embedding                          |
| POST   | `/search`                   | Semantic/hybrid search                               |
| POST   | `/chat`                     | Chat (RAG), streaming via SSE                        |
| POST   | `/agent`                    | Agent invocation                                     |
| GET    | `/conversations`            | List conversations                                   |
| GET    | `/conversations/{id}`       | Conversation detail + messages                       |
| DELETE | `/conversations/{id}`       | Delete conversation                                  |
| POST   | `/feedback`                 | Submit 👍/👎 feedback                                 |
| GET    | `/metrics`                  | Operational metrics                                  |

All routes except `/`, `/health`, and `/ready` require a valid JWT and enforce per-user ownership.

## 20. Troubleshooting

- **`/ready` reports a database error** — check `DATABASE_URL` and confirm migrations have run (`alembic upgrade head`).
- **Embeddings are very slow** — confirm device detection picked CPU as expected on Render (no GPU available there by default); consider a smaller embedding model if latency is unacceptable.
- **CORS errors in the browser** — `CORS_ORIGINS` on the backend must exactly match your frontend's origin (scheme + host, no trailing slash).
- **Render cold starts** — free-tier services sleep after inactivity; the first request after idle will be slow. This is expected, not a bug.

## 21. Security

- JWT auth, bcrypt password hashing, per-user data isolation enforced in the repository layer.
- Strict CORS via env var — never `*` in production.
- File type/size/MIME validation on upload; path-traversal-safe storage keys.
- SQL injection prevented via SQLAlchemy parameterization everywhere.
- The agent's database tool only runs pre-validated `SELECT` statements — `DROP` / `DELETE` / `UPDATE` / `INSERT` / `ALTER` / `TRUNCATE` are blocked.
- Document content is treated as untrusted data (wrapped in `<document_context>` delimiters) and can never override system/tool policy.
- No secrets are committed — see `.gitignore`; never use a `NEXT_PUBLIC_` prefix for anything secret.

## 22. Evaluation

```bash
cd evaluation
python evaluate_retrieval.py --dataset dataset.json
python evaluate_rag.py --dataset dataset.json
```

Extend `dataset.json` with real query / expected-keyword cases from your own documents. Results are written to `evaluation/results/`.

## 23. Known Limitations (read before deploying)

- Free Render/Vercel/Postgres tiers have sleep, CPU, RAM, storage, and bandwidth limits — no tier here is "permanently free" at scale.
- The agent's planner is a lightweight heuristic, not full LLM function-calling — adequate for a first version, but consider replacing it with structured tool-calling for more reliable tool selection.
- Gemini streaming currently falls back to non-streaming internally (see `app/ai/llm/gemini_provider.py`) — swap in true SSE parsing if you need it.
- Hybrid (keyword + vector) search is not yet implemented — current retrieval is vector-only; add a keyword/BM25 pass in `app/ai/retrieval/` as a follow-up.
- No rate-limiting middleware is wired in yet — add one (e.g. `slowapi`) before exposing this publicly.

---

## Project Structure

```
AI-intelligence-System/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/       # health, documents, search, chat, agents, feedback
│   │   ├── api/dependencies.py
│   │   ├── config/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── database/
│   │   ├── security/
│   │   ├── monitoring/
│   │   ├── ai/                # embeddings, llm, rag, retrieval, reranking, agents, prompts
│   │   ├── tools/
│   │   ├── storage/
│   │   └── utils/
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                   # page.tsx, chat/, documents/, search/, settings/, api/
│   ├── components/            # chat/, documents/, search/, ui/, layout/
│   ├── lib/                   # api.ts, auth.ts, config.ts
│   ├── hooks/, types/, public/
│   ├── package.json
│   └── .env.example
├── evaluation/                # dataset.json, evaluate_retrieval.py, evaluate_rag.py, results/
├── docker-compose.yml
├── render.yaml
├── architecture.md
├── README.md
├── .gitignore
└── .github/workflows/ci.yml
```

## Contributing

Issues and pull requests are welcome. Please run the backend lint/type-check/test suite and the frontend lint/build before opening a PR — CI will run the same checks automatically.

## License

No license file is currently included in this repository. Add one (e.g. MIT, Apache-2.0) if you intend for others to reuse this code.