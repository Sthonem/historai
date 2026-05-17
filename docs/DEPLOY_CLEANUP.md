# Deployment cleanup checklist

One-time housekeeping after moving to **Vercel frontend + Vercel backend** (no Railway).

## Vercel — backend project (`historai` / `historai-chi.vercel.app`)

1. Open **Settings → Environment Variables**.
2. Remove **`NEXT_PUBLIC_API_BASE`** if it is still listed. That variable belongs on the **frontend** project only (`NEXT_PUBLIC_API_URL`). It has no effect on the Python backend and only causes confusion.
3. Confirm these remain set:
   - `GROQ_API_KEY`
   - `GEMINI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (Supabase **secret** / service-role key, not the publishable anon key)
   - `CORS_ALLOWED_ORIGINS` = `https://historai-frontend.vercel.app` (and preview URLs if you use branch deploys)
   - `CORS_ALLOWED_ORIGIN_REGEX` = `^https://historai-frontend(-[a-z0-9-]+)*\.vercel\.app$` (optional but recommended)
4. **Redeploy** the backend after env changes (disable “Use existing Build Cache” if you want a clean build).

## Vercel — frontend project (`historai-frontend`)

1. Confirm **`NEXT_PUBLIC_API_URL`** = `https://historai-chi.vercel.app` (no trailing slash).
2. Remove duplicate **`NEXT_PUBLIC_API_BASE`** if both exist — the app accepts either name, but one variable is enough.

## Railway (optional — stop notification emails)

If you created a Railway project during an earlier deploy attempt (e.g. `helpful-rejoicing`):

1. Go to [railway.app](https://railway.app) → open the unused project.
2. **Settings → Danger** → **Delete Project**.

This does not affect Historai on Vercel. It only stops failed-build emails and avoids accidental deploys.

## Duplicate Vercel frontend projects

If you still have old frontend projects (`historai-4ez2`, `historai-fsjb`, etc.), delete them in Vercel so only **`historai-frontend`** remains the production UI.
