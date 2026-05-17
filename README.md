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

The home page groups examples by era (Turkish history, 20th century, early modern, ancient). A few starters:

- What if Atatürk had lived until 1960?
- What if the Ottoman Empire had not entered World War I?
- What if Napoleon had won the Battle of Waterloo?
- What if the Soviet Union had not collapsed in 1991?

## Deploy

See [docs/DEPLOY_CLEANUP.md](docs/DEPLOY_CLEANUP.md) for a short checklist (remove stray env vars, delete unused Railway projects, duplicate Vercel frontends).

You can host both pieces on Vercel as two separate projects (frontend = Next.js, backend = Python serverless), or split frontend on Vercel and backend on Railway (or any host). The Vercel-only path is simpler to manage; the Railway path has no function timeout.

### Option A: Both on Vercel

The backend ships with `api/index.py`, a `vercel.json`, and a `requirements.txt` so Vercel can serve it as a Python serverless function. Because Vercel serverless functions are stateless and time-limited, this mode **requires Supabase** for persistence and is **capped by your Vercel plan's `maxDuration`**:

| Plan | Max function duration | Realistic simulation budget |
| --- | --- | --- |
| Hobby (free) | 60 s | 2-3 turns, 3-4 actors |
| Pro | 300 s (configured) | 6 turns, 6-8 actors |

#### Backend (Vercel project #1)

1. Set up Supabase first (see *Configuration* below) and apply `backend/migrations/001_simulations.sql`.
2. In Vercel, create a new project from this repo with **Root Directory:** `backend`. Framework Preset: **Other**.
3. Add env vars (all required for serverless mode):
   - `GROQ_API_KEY`
   - `GEMINI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (service-role)
   - `CORS_ALLOWED_ORIGINS` — your frontend Vercel URL(s), e.g. `https://historai.vercel.app`
4. Deploy. You'll get a URL like `historai-api.vercel.app`. Hit `/` and verify it returns `{"status":"Historai API is running"}`.

#### Frontend (Vercel project #2)

1. New Vercel project from the same repo with **Root Directory:** `frontend`. Framework Preset: **Next.js** (auto).
2. Env var: `NEXT_PUBLIC_API_URL` = your backend Vercel URL from above (no trailing slash).
3. Deploy.

### Option B: Backend → Railway (no timeout)

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

Other hosts work too — the `Dockerfile` is generic and uses `$PORT`. Render, Fly.io, Google Cloud Run all work the same way. Then set up the frontend on Vercel as in Option A, with `NEXT_PUBLIC_API_URL` pointing at the Railway URL.

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
