# Historai

> What if history had taken a different path?

Historai is a multi-agent AI simulation engine for alternate history. Ask any historical what-if question, and AI-powered historical actors simulate the outcome across multiple turns — producing a detailed narrative report, actor analysis, timeline, and territorial map.

## How It Works

1. **You ask** a what-if historical question
2. **AI generates** 6-8 key historical actors with personas and influence scores
3. **Simulation runs** — actors make decisions, react to each other, and respond to random events
4. **Report is generated** — narrative analysis, actor cards, turn-by-turn timeline, and a territorial control map

## Features

- 🧠 Multi-agent simulation with bilateral interactions and influence scoring
- ⚡ Random event injection for unexpected historical turns
- 🗺️ Territorial control map visualization
- 📜 Turn-by-turn timeline of actor decisions
- 🔄 Groq + Gemini fallback for reliability

## Tech Stack

**Backend**
- FastAPI
- Groq (LLaMA 3.3 70B) + Google Gemini fallback
- Python 3.11+

**Frontend**
- Next.js 16
- Tailwind CSS
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
```

Create `.env`:
```
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
```
```bash
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Example Questions

- What if the Ottoman Empire had not entered World War I?
- What if Julius Caesar had not been assassinated?
- What if Napoleon had won the Battle of Waterloo?
- What if the Soviet Union had not collapsed in 1991?

## Roadmap

- [x] Multi-agent simulation engine
- [x] Narrative report generation
- [x] Actor cards
- [x] Turn-by-turn timeline
- [x] Territorial map visualization
- [ ] Parallel timelines with probability analysis
- [ ] Supabase persistence
- [ ] Auth + simulation limits
- [ ] Deploy

## License

MIT
