'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'

import { listSimulations } from '../lib/api'
import type { SimulationStatus, SimulationSummary } from '../lib/types'

type Filter = 'all' | SimulationStatus

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'done', label: 'Done' },
  { id: 'running', label: 'Running' },
  { id: 'pending', label: 'Pending' },
  { id: 'error', label: 'Failed' },
]

const STATUS_STYLE: Record<SimulationStatus, string> = {
  done: 'bg-emerald-950/40 border-emerald-900/50 text-emerald-300',
  running: 'bg-amber-950/40 border-amber-900/50 text-amber-300',
  pending: 'bg-zinc-900 border-zinc-800 text-zinc-400',
  error: 'bg-rose-950/40 border-rose-900/50 text-rose-300',
}

function formatRelative(iso: string | null | undefined): string {
  if (!iso) return ''
  const ts = new Date(iso).getTime()
  if (Number.isNaN(ts)) return ''
  const diff = Date.now() - ts
  const min = Math.floor(diff / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const d = Math.floor(hr / 24)
  if (d < 7) return `${d}d ago`
  return new Date(iso).toLocaleDateString()
}

export default function HistoryPage() {
  const [items, setItems] = useState<SimulationSummary[] | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    listSimulations()
      .then((data) => {
        if (cancelled) return
        setItems(data.items)
      })
      .catch((err: Error) => {
        if (cancelled) return
        setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    if (!items) return []
    if (filter === 'all') return items
    return items.filter((i) => i.status === filter)
  }, [items, filter])

  return (
    <main className="min-h-screen min-h-[100dvh] bg-[#0a0a0a] text-white">
      <header className="px-4 sm:px-6 py-4 sm:py-5 border-b border-zinc-900 flex items-center justify-between gap-3">
        <Link href="/" className="text-zinc-500 hover:text-white transition text-sm">
          ← Historai
        </Link>
        <span className="text-zinc-600 text-xs">History</span>
      </header>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-8 pb-[max(2rem,env(safe-area-inset-bottom))]">
        <div className="space-y-2">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Past simulations</h1>
          <p className="text-zinc-500 text-sm">
            Every what-if you&apos;ve asked. Pick one to reopen the report.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-3 py-1.5 rounded-full text-xs uppercase tracking-widest border transition-colors ${
                filter === f.id
                  ? 'bg-white text-black border-white'
                  : 'bg-transparent text-zinc-400 border-zinc-800 hover:border-zinc-600'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="border border-rose-900/50 bg-rose-950/30 rounded-2xl p-5 space-y-2">
            <p className="text-[11px] text-rose-400 uppercase tracking-widest">
              Failed to load history
            </p>
            <p className="text-rose-200 text-sm">{error}</p>
          </div>
        )}

        {!items && !error && (
          <div className="flex items-center gap-3 py-8 justify-center">
            <div className="w-5 h-5 border border-zinc-700 border-t-white rounded-full animate-spin" />
            <span className="text-zinc-500 text-sm">Loading history…</span>
          </div>
        )}

        {items && filtered.length === 0 && (
          <div className="border border-zinc-900 bg-zinc-950 rounded-2xl p-10 text-center space-y-2">
            <p className="text-zinc-400">
              {filter === 'all' ? 'No simulations yet.' : `No ${filter} simulations.`}
            </p>
            {filter === 'all' && (
              <Link
                href="/"
                className="inline-block text-sm text-white hover:underline"
              >
                Start your first one →
              </Link>
            )}
          </div>
        )}

        <div className="space-y-2">
          {filtered.map((sim) => {
            const isDone = sim.status === 'done'
            const className = `block border border-zinc-900 ${
              isDone ? 'hover:border-zinc-700' : ''
            } bg-zinc-950 rounded-2xl p-4 transition-colors`
            const body = (
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2 flex-1 min-w-0">
                  <p
                    className={`text-white text-sm leading-snug ${
                      isDone ? '' : 'opacity-70'
                    } line-clamp-2`}
                  >
                    {sim.question}
                  </p>
                  <div className="flex items-center gap-3 text-[11px] text-zinc-600">
                    <span>{sim.turns} turns</span>
                    <span>•</span>
                    <span>{formatRelative(sim.created_at)}</span>
                  </div>
                  {sim.status === 'error' && sim.error && (
                    <p className="text-rose-400 text-xs">{sim.error}</p>
                  )}
                </div>
                <span
                  className={`shrink-0 text-[10px] uppercase tracking-widest border px-2 py-1 rounded-full ${STATUS_STYLE[sim.status]}`}
                >
                  {sim.status}
                </span>
              </div>
            )
            return isDone ? (
              <Link key={sim.id} href={`/report?id=${sim.id}`} className={className}>
                {body}
              </Link>
            ) : (
              <div key={sim.id} className={className}>
                {body}
              </div>
            )
          })}
        </div>
      </div>
    </main>
  )
}
