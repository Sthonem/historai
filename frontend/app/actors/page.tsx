'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { getStatus, runSimulation } from '../lib/api'
import type { Actor } from '../lib/types'

const DEFAULT_TURNS = 6

function ActorsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const simulationId = searchParams.get('id')
  const question = searchParams.get('question')
  const turnsParam = searchParams.get('turns')
  const turns = turnsParam ? Number(turnsParam) || DEFAULT_TURNS : DEFAULT_TURNS

  const [actors, setActors] = useState<Actor[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!simulationId) return
    let cancelled = false

    getStatus(simulationId)
      .then((data) => {
        if (cancelled) return
        setActors(data.actors)
      })
      .catch((err: Error) => {
        if (cancelled) return
        setError(err.message)
      })

    return () => {
      cancelled = true
    }
  }, [simulationId])

  const handleRun = async () => {
    if (!simulationId) return
    setLoading(true)
    setError(null)
    try {
      await runSimulation(simulationId, actors, turns)
      router.push(`/simulation?id=${simulationId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start simulation')
      setLoading(false)
    }
  }

  const influenceColor = (n: number) => {
    if (n >= 9) return 'text-amber-400'
    if (n >= 7) return 'text-zinc-200'
    return 'text-zinc-400'
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="px-6 py-5 border-b border-zinc-900 flex items-center justify-between">
        <Link href="/" className="text-zinc-500 hover:text-white transition text-sm">← Historai</Link>
        <span className="text-zinc-600 text-xs">Step 1 of 2</span>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10 space-y-10">

        <div className="space-y-1">
          <p className="text-xs text-zinc-600 uppercase tracking-widest">Your question</p>
          <h2 className="text-xl text-zinc-200 font-medium leading-snug">&ldquo;{question}&rdquo;</h2>
          <Link
            href="/"
            className="inline-block text-xs text-zinc-500 hover:text-white transition pt-1"
          >
            ← Change question
          </Link>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <h1 className="text-xs uppercase tracking-widest text-zinc-500 font-medium">Historical actors</h1>
            <div className="flex-1 h-px bg-zinc-900" />
            {actors.length > 0 && (
              <span className="text-xs text-zinc-600">{actors.length} actors</span>
            )}
          </div>

          {error && (
            <p className="text-xs text-rose-400">{error}</p>
          )}

          {actors.length === 0 && !error ? (
            <div className="flex items-center gap-3 py-8 justify-center">
              <div className="w-5 h-5 border border-zinc-700 border-t-white rounded-full animate-spin" />
              <span className="text-zinc-500 text-sm">Identifying key historical figures...</span>
            </div>
          ) : (
            <div className="space-y-2">
              {actors.map((actor) => (
                <div
                  key={`${actor.name}-${actor.faction}`}
                  className="border border-zinc-900 hover:border-zinc-800 rounded-2xl p-4 flex items-start justify-between gap-4 transition-colors bg-zinc-950"
                >
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-white">{actor.name}</span>
                      <span className="text-[11px] text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-full shrink-0">
                        {actor.faction}
                      </span>
                    </div>
                    <p className="text-zinc-500 text-sm">{actor.role}</p>
                    <p className="text-zinc-400 text-sm leading-relaxed">{actor.motivation}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[10px] text-zinc-600 uppercase tracking-wider mb-0.5">influence</p>
                    <p className={`text-2xl font-bold ${influenceColor(actor.influence)}`}>
                      {actor.influence}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {actors.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs text-zinc-600 text-center">
              These actors will simulate {turns} {turns === 1 ? 'turn' : 'turns'} of alternate history
            </p>
            <button
              onClick={handleRun}
              disabled={loading}
              className="w-full bg-white text-black font-semibold py-3.5 rounded-2xl hover:bg-zinc-100 transition disabled:opacity-30 text-[15px]"
            >
              {loading ? 'Starting simulation...' : 'Run simulation →'}
            </button>
          </div>
        )}

      </div>
    </main>
  )
}

export default function ActorsPage() {
  return (
    <Suspense>
      <ActorsContent />
    </Suspense>
  )
}
