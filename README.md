# Historai

> What if history had taken a different path?

Historai is a multi-agent AI simulation engine for alternate history. Ask any historical what-if question, and AI-powered historical actors simulate the outcome across multiple turns — producing a detailed narrative report, actor analysis, timeline, and territorial map.

## How It Works

1. **You ask** a what-if historical question
2. **AI generates** 6-8 key historical actors with personas and influence scores
3. **Simulation runs** — actors make decisions, react to each other, and respond to random events
4. **Report is generated** — narrative analysis, actor cards, turn-by-turn timeline, and a territorial control map

## Features

- Multi-agent simulation with influence-weighted turn order and per-actor memory
- Random event injection for unexpected historical turns
- Configurable number of simulation turns (1–20)
- Territorial control map visualization with modern country names
- Turn-by-turn timeline of actor decisions
- Groq (LLaMA 3.3 70B) primary with Gemini fallback for reliability

## Tech Stack

**Backend**
- FastAPI
- Groq + Google Gemini fallback
- Python 3.11+

**Frontend**
- Next.js 16 (App Router)
- Tailwind CSS v4
- React Simple Maps

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key → [groq.com](https://groq.com)
- Gemini API key → [aistudio.google.com](https://aistudio.google.com)

### Backend

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e .
cp .env.example .env  # then fill in your keys
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.example .env.local  # optional; defaults to http://localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Configuration

Backend (`.env`):

| Variable | Default | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | — | Required. Groq API key. |
| `GEMINI_API_KEY` | — | Required. Gemini API key for fallback. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins. |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model id. |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model id. |
| `LLM_TEMPERATURE` | `0.7` | Sampling temperature. |
| `LLM_MAX_TOKENS` | `800` | Max tokens per Groq call. |
| `SUPABASE_URL` | unset | Optional. If set with `SUPABASE_KEY`, simulations persist to Supabase. |
| `SUPABASE_KEY` | unset | Optional. Service-role key (not the anon key). |

If you set the Supabase variables, apply `backend/migrations/001_simulations.sql` against your project once (Supabase SQL editor works fine). Without those variables, simulations live in process memory and disappear on restart.

Frontend (`.env.local`):

| Variable | Default | Description |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Historai backend URL. |

## Example Questions

- What if the Ottoman Empire had not entered World War I?
- What if Julius Caesar had not been assassinated?
- What if Napoleon had won the Battle of Waterloo?
- What if the Soviet Union had not collapsed in 1991?

## Deploy

The app has two pieces: a Next.js frontend (serves fine on Vercel) and a long-running FastAPI backend (needs a regular server because of SSE streaming and per-process in-memory state).

### Backend → Railway (recommended)

1. Sign in at [railway.app](https://railway.app) and create a new project from this GitHub repo.
2. In the service settings:
   - **Root Directory:** `backend`
   - Railway will detect the `Dockerfile` automatically.
3. Add environment variables under **Variables**:
   - `GROQ_API_KEY`
   - `GEMINI_API_KEY`
   - `CORS_ALLOWED_ORIGINS` — comma-separated list of your Vercel URLs (e.g. `https://historai.vercel.app,https://historai-git-main-you.vercel.app`)
   - Optionally `SUPABASE_URL` and `SUPABASE_KEY` (service-role) to persist
4. Click **Generate Domain** under Settings → Networking. You'll get something like `historai-backend-production.up.railway.app`.
5. Once live, hit `https://YOUR-DOMAIN/` and confirm it returns `{"status":"Historai API is running"}`.

Other hosts work too — the `Dockerfile` is generic and uses `$PORT`. Render, Fly.io, Google Cloud Run all work the same way.

### Frontend → Vercel

1. Sign in at [vercel.com](https://vercel.com) and import this GitHub repo.
2. In the project settings:
   - **Root Directory:** `frontend`
   - Vercel will detect Next.js automatically.
3. Add an environment variable:
   - `NEXT_PUBLIC_API_URL` = your Railway URL from above (no trailing slash)
4. Deploy. Vercel gives you a URL like `historai.vercel.app`.

After deploying the frontend, go back to Railway and update `CORS_ALLOWED_ORIGINS` to include the actual Vercel URL, then redeploy the backend.

## Roadmap

- [x] Multi-agent simulation engine
- [x] Narrative report generation
- [x] Actor cards
- [x] Turn-by-turn timeline
- [x] Territorial map visualization
- [x] Configurable simulation length
- [x] Supabase persistence + history page
- [x] Deploy guide (Vercel + Railway)
- [ ] Parallel timelines with probability analysis
- [ ] Auth + simulation limits

## License

MIT
