'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import dynamic from 'next/dynamic'

import { ApiError, getReport } from '../lib/api'
import type { Report } from '../lib/types'

const HistoryMap = dynamic(() => import('../components/HistoryMap'), { ssr: false })

const INITIAL_DELAY_MS = 2000
const MAX_DELAY_MS = 15000

function ReportContent() {
  const searchParams = useSearchParams()
  const simulationId = searchParams.get('id')
  const [report, setReport] = useState<Report | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!simulationId) return
    let cancelled = false
    let delay = INITIAL_DELAY_MS

    const fetchReport = async () => {
      try {
        const data = await getReport(simulationId)
        if (cancelled) return
        setReport(data)
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 425) {
          delay = Math.min(delay * 1.5, MAX_DELAY_MS)
          setTimeout(fetchReport, delay)
          return
        }
        if (err instanceof ApiError && err.status === 500) {
          setError(err.message)
          return
        }
        delay = Math.min(delay * 1.5, MAX_DELAY_MS)
        setTimeout(fetchReport, delay)
      }
    }

    fetchReport()
    return () => {
      cancelled = true
    }
  }, [simulationId])

  if (error) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center px-4">
        <div className="max-w-md text-center space-y-3">
          <p className="text-rose-400 text-sm uppercase tracking-widest">Simulation failed</p>
          <p className="text-zinc-300 text-sm">{error}</p>
          <Link href="/" className="inline-block text-xs text-zinc-500 hover:text-white transition">
            ← Run another simulation
          </Link>
        </div>
      </main>
    )
  }

  if (!report) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border border-zinc-700 border-t-white rounded-full animate-spin mx-auto" />
          <p className="text-zinc-500 text-sm">Loading report...</p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="border-b border-zinc-900 px-6 py-4 flex items-center justify-between">
        <Link href="/" className="text-zinc-500 hover:text-white transition text-sm flex items-center gap-2">
          ← Historai
        </Link>
        <span className="text-zinc-600 text-xs">Alternate history report</span>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-12 space-y-16">

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-emerald-500 text-xs uppercase tracking-widest font-medium">Simulation complete</span>
          </div>
          <h1 className="text-3xl font-bold leading-tight tracking-tight">
            {report.question}
          </h1>
        </div>

        {report.map_data && report.map_data.factions.length > 0 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <h2 className="text-xs uppercase tracking-widest text-zinc-500 font-medium">Territorial control</h2>
              <div className="flex-1 h-px bg-zinc-900" />
            </div>
            <HistoryMap mapData={report.map_data} />
          </div>
        )}

        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <h2 className="text-xs uppercase tracking-widest text-zinc-500 font-medium">Analysis</h2>
            <div className="flex-1 h-px bg-zinc-900" />
          </div>
          <div className="space-y-5">
            {report.narrative.split('\n\n').map((para, i) => (
              <p key={i} className="text-zinc-300 leading-relaxed text-[15px]">{para}</p>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <h2 className="text-xs uppercase tracking-widest text-zinc-500 font-medium">Key actors</h2>
            <div className="flex-1 h-px bg-zinc-900" />
          </div>
          <div className="space-y-3">
            {report.actor_cards.map((actor) => (
              <div
                key={`${actor.name}-${actor.faction}`}
                className="group border border-zinc-900 hover:border-zinc-700 rounded-2xl p-5 transition-all duration-200 bg-zinc-950"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white">{actor.name}</span>
                      <span className="text-[11px] text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-full">
                        {actor.faction}
                      </span>
                    </div>
                    <p className="text-zinc-500 text-sm">{actor.role}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] text-zinc-600 uppercase tracking-wider">influence</p>
                    <p className="text-2xl font-bold text-white">{actor.influence}</p>
                  </div>
                </div>
                <p className="text-zinc-400 text-sm leading-relaxed">{actor.summary}</p>
              </div>
            ))}
          </div>
        </div>

        {report.timeline && report.timeline.length > 0 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <h2 className="text-xs uppercase tracking-widest text-zinc-500 font-medium">Timeline</h2>
              <div className="flex-1 h-px bg-zinc-900" />
            </div>
            <div className="space-y-4">
              {report.timeline.map((turn) => (
                <div key={turn.turn} className="border border-zinc-900 bg-zinc-950 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-zinc-600" />
                    <span className="text-xs text-zinc-500 uppercase tracking-widest font-medium">
                      Turn {turn.turn}
                    </span>
                  </div>

                  {turn.event && (
                    <div className="flex items-start gap-2 bg-amber-950/30 border border-amber-900/30 rounded-xl px-3 py-2">
                      <span className="text-amber-500 text-xs mt-0.5">⚡</span>
                      <p className="text-amber-400 text-sm">{turn.event}</p>
                    </div>
                  )}

                  <div className="space-y-3">
                    {Object.entries(turn.decisions).map(([actor, decision]) => (
                      <div key={actor} className="flex items-start gap-4 py-2 border-b border-zinc-900 last:border-0">
                        <span className="text-zinc-500 text-sm shrink-0 w-36 truncate pt-0.5">{actor}</span>
                        <span className="text-zinc-300 text-sm leading-relaxed">{decision}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-8 border-t border-zinc-900 flex items-center justify-between">
          <Link href="/" className="text-sm text-zinc-500 hover:text-white transition">
            ← Run another simulation
          </Link>
          <span className="text-xs text-zinc-700">Powered by Historai</span>
        </div>

      </div>
    </main>
  )
}

export default function ReportPage() {
  return (
    <Suspense>
      <ReportContent />
    </Suspense>
  )
}
