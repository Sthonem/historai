'use client'

import { Suspense, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import dynamic from 'next/dynamic'

import { ApiError, getReport } from '../lib/api'
import type { ActorCard, Report, TimelineTurn } from '../lib/types'

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
    <main className="min-h-screen min-h-[100dvh] bg-[#0a0a0a] text-white">
      <header className="border-b border-zinc-900 px-4 sm:px-6 py-4 flex items-center justify-between gap-3">
        <Link href="/" className="text-zinc-500 hover:text-white transition text-sm flex items-center gap-2">
          ← Historai
        </Link>
        <span className="text-zinc-600 text-xs shrink-0 hidden sm:inline">Alternate history report</span>
      </header>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-10 sm:space-y-14 pb-[max(2rem,env(safe-area-inset-bottom))]">

        <Hero question={report.question} narrative={report.narrative} />

        <MapOrBalance report={report} />

        <Section title="Analysis">
          <Narrative text={report.narrative} />
        </Section>

        <Section title="Key actors" trailing={`${report.actor_cards.length} actors`}>
          <div className="space-y-2">
            {report.actor_cards.map((actor, idx) => (
              <ActorRow
                key={`${actor.name}-${actor.faction}`}
                actor={actor}
                defaultOpen={idx === 0}
              />
            ))}
          </div>
        </Section>

        {report.timeline && report.timeline.length > 0 && (
          <Section title="Timeline" trailing={`${report.timeline.length} turns`}>
            <div className="space-y-2">
              {report.timeline.map((turn, idx) => (
                <TimelineRow key={turn.turn} turn={turn} defaultOpen={idx === 0} />
              ))}
            </div>
          </Section>
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

function MapOrBalance({ report }: { report: Report }) {
  const totalCountries = report.map_data?.factions.reduce(
    (acc, f) => acc + (f.countries?.length ?? 0),
    0,
  ) ?? 0
  const mapIsViable =
    !!report.map_data &&
    report.map_data.factions.length >= 2 &&
    totalCountries >= 4

  if (mapIsViable) {
    return (
      <Section title="Territorial control" trailing={report.map_data?.year ?? undefined}>
        <HistoryMap mapData={report.map_data} />
      </Section>
    )
  }

  const balance = factionPowerBalance(report.actor_cards)
  if (balance.length === 0) return null

  const max = Math.max(...balance.map((b) => b.power))
  return (
    <Section title="Power balance" trailing="influence by faction">
      <div className="space-y-3">
        {balance.map((row) => {
          const pct = max > 0 ? (row.power / max) * 100 : 0
          return (
            <div key={row.faction} className="space-y-1.5">
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="text-zinc-200 truncate">{row.faction}</span>
                <span className="text-zinc-500 text-xs tabular-nums shrink-0">
                  {row.power} · {row.actors} actor{row.actors === 1 ? '' : 's'}
                </span>
              </div>
              <div className="h-1.5 bg-zinc-900 rounded-full overflow-hidden">
                <div
                  className="h-full bg-zinc-400"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
        <p className="text-[11px] text-zinc-600 pt-2">
          This scenario doesn&rsquo;t cleanly map to territory, so we&rsquo;re showing
          which factions hold the most weight instead.
        </p>
      </div>
    </Section>
  )
}

function factionPowerBalance(
  actors: ActorCard[],
): { faction: string; power: number; actors: number }[] {
  const byFaction = new Map<string, { power: number; actors: number }>()
  for (const a of actors) {
    const key = a.faction || 'Independent'
    const cur = byFaction.get(key) ?? { power: 0, actors: 0 }
    cur.power += a.influence
    cur.actors += 1
    byFaction.set(key, cur)
  }
  return Array.from(byFaction.entries())
    .map(([faction, v]) => ({ faction, ...v }))
    .sort((a, b) => b.power - a.power)
}

function Hero({ question, narrative }: { question: string; narrative: string }) {
  const tldr = useMemo(() => deriveTldr(narrative), [narrative])
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        <span className="text-emerald-500 text-xs uppercase tracking-widest font-medium">Simulation complete</span>
      </div>
      <h1 className="text-2xl sm:text-3xl font-bold leading-tight tracking-tight break-words">{question}</h1>
      {tldr && (
        <p className="text-zinc-300 text-[15px] leading-relaxed border-l-2 border-zinc-700 pl-4">
          {tldr}
        </p>
      )}
    </div>
  )
}

function Section({
  title,
  trailing,
  children,
}: {
  title: string
  trailing?: string | null
  children: React.ReactNode
}) {
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <h2 className="text-xs uppercase tracking-widest text-zinc-500 font-medium">{title}</h2>
        <div className="flex-1 h-px bg-zinc-900" />
        {trailing && <span className="text-[11px] text-zinc-600">{trailing}</span>}
      </div>
      {children}
    </div>
  )
}

function Narrative({ text }: { text: string }) {
  const paragraphs = useMemo(() => text.split(/\n\n+/).filter((p) => p.trim().length > 0), [text])
  const [expanded, setExpanded] = useState(false)
  const showToggle = paragraphs.length > 1
  const visible = expanded || !showToggle ? paragraphs : paragraphs.slice(0, 1)
  return (
    <div className="space-y-5">
      {visible.map((para, i) => (
        <p key={i} className="text-zinc-300 leading-relaxed text-[15px]">
          {para}
        </p>
      ))}
      {showToggle && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-zinc-500 hover:text-white transition tracking-wide"
        >
          {expanded ? '— Show less' : `↓ Read full analysis (${paragraphs.length - 1} more)`}
        </button>
      )}
    </div>
  )
}

function ActorRow({ actor, defaultOpen = false }: { actor: ActorCard; defaultOpen?: boolean }) {
  return (
    <details
      open={defaultOpen}
      className="group rounded-2xl bg-zinc-950 border border-zinc-900 open:border-zinc-700 transition-colors"
    >
      <summary className="cursor-pointer list-none p-4 flex items-center gap-4">
        <span className="w-9 h-9 shrink-0 rounded-full bg-zinc-900 border border-zinc-800 grid place-items-center text-zinc-400 text-sm font-medium">
          {initials(actor.name)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-white truncate">{actor.name}</span>
            <span className="text-[10px] text-zinc-500 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded-full">
              {actor.faction}
            </span>
          </div>
          <p className="text-zinc-500 text-xs truncate">{actor.role}</p>
        </div>
        <InfluenceBar value={actor.influence} />
        <span className="text-zinc-600 group-open:rotate-180 transition-transform text-xs">▾</span>
      </summary>
      <div className="px-4 pb-4 pt-0">
        <div className="ml-[52px] border-t border-zinc-900 pt-3">
          <p className="text-zinc-400 text-sm leading-relaxed">{actor.summary}</p>
        </div>
      </div>
    </details>
  )
}

function InfluenceBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(10, value)) * 10
  return (
    <div className="flex items-center gap-2 shrink-0">
      <div className="w-16 h-1 bg-zinc-900 rounded-full overflow-hidden">
        <div
          className="h-full bg-zinc-400"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-zinc-400 text-xs tabular-nums w-4 text-right">{value}</span>
    </div>
  )
}

function TimelineRow({
  turn,
  defaultOpen = false,
}: {
  turn: TimelineTurn
  defaultOpen?: boolean
}) {
  const decisionCount = Object.keys(turn.decisions).length
  return (
    <details
      open={defaultOpen}
      className="group rounded-2xl bg-zinc-950 border border-zinc-900 open:border-zinc-700 transition-colors"
    >
      <summary className="cursor-pointer list-none p-4 flex items-start gap-3">
        <div className="w-7 h-7 shrink-0 rounded-full bg-zinc-900 border border-zinc-800 grid place-items-center text-zinc-400 text-xs font-medium">
          {turn.turn}
        </div>
        <div className="min-w-0 flex-1 space-y-1">
          {turn.event ? (
            <p className="text-amber-300 text-sm leading-snug flex items-start gap-1.5">
              <span className="text-amber-500 mt-0.5">⚡</span>
              <span>{turn.event}</span>
            </p>
          ) : (
            <p className="text-zinc-500 text-sm italic">Quiet turn — no major event</p>
          )}
          <p className="text-zinc-600 text-xs">{decisionCount} decision{decisionCount === 1 ? '' : 's'}</p>
        </div>
        <span className="text-zinc-600 group-open:rotate-180 transition-transform text-xs mt-1">▾</span>
      </summary>
      <div className="px-4 pb-4 pt-0">
        <div className="ml-10 border-t border-zinc-900 pt-3 space-y-3">
          {Object.entries(turn.decisions).map(([actor, decision]) => (
            <div key={actor} className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4">
              <span className="text-zinc-500 text-xs shrink-0 sm:w-32 sm:truncate pt-0.5">{actor}</span>
              <span className="text-zinc-300 text-sm leading-relaxed">{decision}</span>
            </div>
          ))}
        </div>
      </div>
    </details>
  )
}

function deriveTldr(narrative: string): string | null {
  const firstParagraph = narrative.split(/\n\n+/)[0]?.trim()
  if (!firstParagraph) return null
  const sentences = firstParagraph.match(/[^.!?]+[.!?]+/g)
  if (!sentences || sentences.length === 0) {
    return firstParagraph.length > 220 ? firstParagraph.slice(0, 220).trim() + '…' : firstParagraph
  }
  const first = sentences[0].trim()
  if (first.length > 180 || sentences.length === 1) return first
  return (first + ' ' + sentences[1].trim()).trim()
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

export default function ReportPage() {
  return (
    <Suspense>
      <ReportContent />
    </Suspense>
  )
}
