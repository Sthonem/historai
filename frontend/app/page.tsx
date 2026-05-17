'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

import { initSimulation } from './lib/api'
import {
  EXAMPLE_CATEGORIES,
  type ExampleCategoryId,
} from './lib/exampleQuestions'

const DEFAULT_TURNS = 1
const DEFAULT_CATEGORY: ExampleCategoryId = 'turkish'

export default function Home() {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState(DEFAULT_TURNS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exampleCategory, setExampleCategory] = useState<ExampleCategoryId>(DEFAULT_CATEGORY)
  const router = useRouter()

  const activeExamples =
    EXAMPLE_CATEGORIES.find((c) => c.id === exampleCategory)?.examples ?? []

  const handleSubmit = async (q?: string) => {
    const finalQuestion = (q ?? question).trim()
    if (!finalQuestion) return
    setLoading(true)
    setError(null)

    try {
      const data = await initSimulation(finalQuestion, turns)
      const params = new URLSearchParams({
        id: data.simulation_id,
        question: finalQuestion,
        turns: String(turns),
      })
      router.push(`/actors?${params.toString()}`)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen min-h-[100dvh] bg-[#0a0a0a] text-white flex flex-col">
      <header className="px-4 sm:px-6 py-4 sm:py-5 border-b border-zinc-900 flex items-center justify-between gap-3">
        <span className="text-white font-semibold tracking-tight">Historai</span>
        <Link
          href="/history"
          className="text-zinc-500 hover:text-white transition text-xs uppercase tracking-widest py-2 -my-2"
        >
          History
        </Link>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-10 sm:py-20 pb-[max(2.5rem,env(safe-area-inset-bottom))]">
        <div className="max-w-2xl w-full space-y-8 sm:space-y-10">

          <section className="space-y-3 sm:space-y-4 text-center">
            <div className="inline-flex items-center gap-2 border border-zinc-800 rounded-full px-3 py-1 text-xs text-zinc-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" aria-hidden />
              Multi-agent AI simulation
            </div>
            <h1 className="text-3xl sm:text-5xl font-bold tracking-tight leading-tight">
              What if history<br />took a different path?
            </h1>
            <p className="text-zinc-500 text-base sm:text-lg px-1">
              Ask any historical what-if question. AI agents simulate the outcome.
            </p>
          </section>

          <section className="space-y-3">
            <textarea
              className="w-full bg-zinc-900 border border-zinc-800 focus:border-zinc-600 rounded-2xl p-4 text-white placeholder-zinc-600 resize-none focus:outline-none text-base transition-colors min-h-[5.5rem]"
              rows={3}
              placeholder="What if the Ottoman Empire had not entered World War I?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
            />

            <div className="space-y-2 px-1">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
                <label className="text-xs text-zinc-500 uppercase tracking-widest shrink-0" htmlFor="turns">
                  Turns
                </label>
                <div className="flex items-center gap-3 w-full sm:flex-1 sm:max-w-xs">
                  <input
                    id="turns"
                    type="range"
                    min={1}
                    max={12}
                    value={turns}
                    onChange={(e) => setTurns(Number(e.target.value))}
                    className="flex-1 accent-white min-h-[44px] sm:min-h-0"
                  />
                  <span className="text-sm text-zinc-300 tabular-nums w-6 text-right shrink-0">{turns}</span>
                </div>
              </div>
              <p className="text-[11px] text-zinc-600 leading-relaxed">
                Tip: keep it at <span className="text-zinc-400">1 turn</span> while trying things
                out — each extra turn calls the LLM once per actor and burns tokens fast.
              </p>
            </div>

            <button
              type="button"
              onClick={() => handleSubmit()}
              disabled={loading || !question.trim()}
              className="w-full bg-white text-black font-semibold py-3.5 min-h-[48px] rounded-2xl hover:bg-zinc-100 active:bg-zinc-200 transition disabled:opacity-30 disabled:cursor-not-allowed text-[15px]"
            >
              {loading ? 'Generating actors...' : 'Simulate →'}
            </button>

            {error && <p className="text-xs text-rose-400 text-center">{error}</p>}
          </section>

          <section className="space-y-3">
            <p className="text-xs text-zinc-600 uppercase tracking-widest text-center">Try an example</p>
            <div
              className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
              role="tablist"
              aria-label="Example categories"
            >
              {EXAMPLE_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  role="tab"
                  aria-selected={exampleCategory === cat.id}
                  onClick={() => setExampleCategory(cat.id)}
                  disabled={loading}
                  className={`shrink-0 px-3 py-2 min-h-[40px] rounded-full text-xs uppercase tracking-widest border transition-colors disabled:opacity-30 ${
                    exampleCategory === cat.id
                      ? 'bg-white text-black border-white'
                      : 'bg-transparent text-zinc-400 border-zinc-800 hover:border-zinc-600'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-1 gap-2">
              {activeExamples.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => handleSubmit(ex)}
                  disabled={loading}
                  className="text-left text-sm text-zinc-400 hover:text-white border border-zinc-900 hover:border-zinc-700 active:border-zinc-600 rounded-xl px-4 py-3.5 min-h-[48px] transition-all disabled:opacity-30"
                >
                  {ex}
                </button>
              ))}
            </div>
          </section>

        </div>
      </div>
    </main>
  )
}
