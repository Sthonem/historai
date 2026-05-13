'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

import { initSimulation } from './lib/api'

const EXAMPLES = [
  'What if the Ottoman Empire had not entered World War I?',
  'What if Napoleon had won the Battle of Waterloo?',
  'What if the Soviet Union had not collapsed in 1991?',
  'What if Julius Caesar had not been assassinated?',
]

const DEFAULT_TURNS = 6

export default function Home() {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState(DEFAULT_TURNS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

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
    <main className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      <div className="px-6 py-5 border-b border-zinc-900 flex items-center justify-between">
        <span className="text-white font-semibold tracking-tight">Historai</span>
        <Link
          href="/history"
          className="text-zinc-500 hover:text-white transition text-xs uppercase tracking-widest"
        >
          History
        </Link>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-4 py-20">
        <div className="max-w-2xl w-full space-y-10">

          <div className="space-y-4 text-center">
            <div className="inline-flex items-center gap-2 border border-zinc-800 rounded-full px-3 py-1 text-xs text-zinc-400">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Multi-agent AI simulation
            </div>
            <h1 className="text-5xl font-bold tracking-tight leading-tight">
              What if history<br />took a different path?
            </h1>
            <p className="text-zinc-500 text-lg">
              Ask any historical what-if question. AI agents simulate the outcome.
            </p>
          </div>

          <div className="space-y-3">
            <textarea
              className="w-full bg-zinc-900 border border-zinc-800 focus:border-zinc-600 rounded-2xl p-4 text-white placeholder-zinc-600 resize-none focus:outline-none text-base transition-colors"
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

            <div className="flex items-center justify-between gap-3 px-1">
              <label className="text-xs text-zinc-500 uppercase tracking-widest" htmlFor="turns">
                Turns
              </label>
              <div className="flex items-center gap-3 flex-1 max-w-xs">
                <input
                  id="turns"
                  type="range"
                  min={1}
                  max={12}
                  value={turns}
                  onChange={(e) => setTurns(Number(e.target.value))}
                  className="flex-1 accent-white"
                />
                <span className="text-sm text-zinc-300 tabular-nums w-6 text-right">{turns}</span>
              </div>
            </div>

            <button
              onClick={() => handleSubmit()}
              disabled={loading || !question.trim()}
              className="w-full bg-white text-black font-semibold py-3.5 rounded-2xl hover:bg-zinc-100 transition disabled:opacity-30 disabled:cursor-not-allowed text-[15px]"
            >
              {loading ? 'Generating actors...' : 'Simulate →'}
            </button>

            {error && (
              <p className="text-xs text-rose-400 text-center">{error}</p>
            )}
          </div>

          <div className="space-y-2">
            <p className="text-xs text-zinc-600 uppercase tracking-widest text-center">Try an example</p>
            <div className="grid grid-cols-1 gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => handleSubmit(ex)}
                  disabled={loading}
                  className="text-left text-sm text-zinc-400 hover:text-white border border-zinc-900 hover:border-zinc-700 rounded-xl px-4 py-3 transition-all disabled:opacity-30"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

        </div>
      </div>
    </main>
  )
}
