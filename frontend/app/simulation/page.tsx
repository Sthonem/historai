'use client'

import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { streamUrl } from '../lib/api'
import type { StreamEvent } from '../lib/types'

type Phase = 'connecting' | 'simulating' | 'generating_report' | 'done' | 'error'

interface ActorLine {
  actor: string
  decision?: string
  thinking: boolean
}

interface TurnView {
  turn: number
  event?: string
  lines: ActorLine[]
  completed: boolean
}

function SimulationContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const simulationId = searchParams.get('id')

  const [phase, setPhase] = useState<Phase>('connecting')
  const [turns, setTurns] = useState<TurnView[]>([])
  const [totalTurns, setTotalTurns] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const turnsRef = useRef<TurnView[]>([])
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    turnsRef.current = turns
  }, [turns])

  useEffect(() => {
    if (!simulationId) return

    const source = new EventSource(streamUrl(simulationId))

    const handle = (raw: MessageEvent) => {
      let evt: StreamEvent
      try {
        evt = JSON.parse(raw.data)
      } catch {
        return
      }
      applyEvent(evt)
    }

    const eventTypes: StreamEvent['type'][] = [
      'simulation_started',
      'turn_started',
      'event_injected',
      'actor_thinking',
      'actor_decided',
      'turn_completed',
      'simulation_completed',
      'report_generating',
      'done',
      'error',
    ]
    eventTypes.forEach((t) => source.addEventListener(t, handle as EventListener))

    source.onerror = () => {
      if (source.readyState === EventSource.CLOSED) {
        source.close()
      }
    }

    function applyEvent(evt: StreamEvent) {
      if (evt.type === 'simulation_started') {
        setTotalTurns(evt.turns)
        setPhase('simulating')
        return
      }
      if (evt.type === 'turn_started') {
        setPhase('simulating')
        setTurns((prev) => {
          if (prev.some((t) => t.turn === evt.turn)) return prev
          return [...prev, { turn: evt.turn, lines: [], completed: false }]
        })
        return
      }
      if (evt.type === 'event_injected') {
        setTurns((prev) =>
          prev.map((t) => (t.turn === evt.turn ? { ...t, event: evt.event } : t)),
        )
        return
      }
      if (evt.type === 'actor_thinking') {
        setTurns((prev) =>
          prev.map((t) => {
            if (t.turn !== evt.turn) return t
            if (t.lines.some((l) => l.actor === evt.actor)) return t
            return { ...t, lines: [...t.lines, { actor: evt.actor, thinking: true }] }
          }),
        )
        return
      }
      if (evt.type === 'actor_decided') {
        setTurns((prev) =>
          prev.map((t) => {
            if (t.turn !== evt.turn) return t
            const lines = t.lines.map((l) =>
              l.actor === evt.actor ? { ...l, decision: evt.decision, thinking: false } : l,
            )
            return { ...t, lines }
          }),
        )
        return
      }
      if (evt.type === 'turn_completed') {
        setTurns((prev) =>
          prev.map((t) => (t.turn === evt.turn ? { ...t, completed: true } : t)),
        )
        return
      }
      if (evt.type === 'report_generating') {
        setPhase('generating_report')
        return
      }
      if (evt.type === 'done') {
        setPhase('done')
        source.close()
        router.push(`/report?id=${evt.simulation_id}`)
        return
      }
      if (evt.type === 'error') {
        setPhase('error')
        setError(evt.error)
        source.close()
      }
    }

    return () => {
      source.close()
    }
  }, [simulationId, router])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turns])

  const headline = useMemo(() => {
    if (phase === 'error') return 'Simulation failed'
    if (phase === 'connecting') return 'Connecting…'
    if (phase === 'generating_report') return 'Writing the final report…'
    if (phase === 'done') return 'Done — opening report…'
    const current = turns[turns.length - 1]
    if (!current) return 'Starting simulation…'
    return totalTurns
      ? `Turn ${current.turn} of ${totalTurns}`
      : `Turn ${current.turn}`
  }, [phase, turns, totalTurns])

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="px-6 py-5 border-b border-zinc-900 flex items-center justify-between">
        <Link href="/" className="text-zinc-500 hover:text-white transition text-sm">
          ← Historai
        </Link>
        <span className="text-zinc-600 text-xs">Live simulation</span>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10 space-y-8">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                phase === 'error'
                  ? 'bg-rose-500'
                  : phase === 'done'
                  ? 'bg-emerald-500'
                  : 'bg-amber-400 animate-pulse'
              }`}
            />
            <span className="text-xs uppercase tracking-widest text-zinc-500">{headline}</span>
          </div>
          {totalTurns !== null && (
            <div className="w-full h-1 bg-zinc-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-white transition-all duration-500"
                style={{
                  width: `${Math.min(
                    100,
                    (turns.filter((t) => t.completed).length / totalTurns) * 100,
                  )}%`,
                }}
              />
            </div>
          )}
        </div>

        {error && (
          <div className="border border-rose-900/50 bg-rose-950/30 rounded-2xl p-5 space-y-2">
            <p className="text-[11px] text-rose-400 uppercase tracking-widest">
              Simulation failed
            </p>
            <p className="text-rose-200 text-sm">{error}</p>
            <Link
              href="/"
              className="inline-block text-xs text-rose-300 hover:text-white transition"
            >
              ← Try again
            </Link>
          </div>
        )}

        <div className="space-y-4">
          {turns.length === 0 && phase !== 'error' && (
            <div className="flex items-center gap-3 py-12 justify-center">
              <div className="w-5 h-5 border border-zinc-700 border-t-white rounded-full animate-spin" />
              <span className="text-zinc-500 text-sm">Waiting for the first turn…</span>
            </div>
          )}

          {turns.map((turn) => (
            <div
              key={turn.turn}
              className="border border-zinc-900 bg-zinc-950 rounded-2xl p-5 space-y-4"
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-1.5 h-1.5 rounded-full ${
                    turn.completed ? 'bg-emerald-500' : 'bg-amber-400 animate-pulse'
                  }`}
                />
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
                {turn.lines.map((line) => (
                  <div
                    key={line.actor}
                    className="flex items-start gap-4 py-2 border-b border-zinc-900 last:border-0"
                  >
                    <span className="text-zinc-500 text-sm shrink-0 w-36 truncate pt-0.5">
                      {line.actor}
                    </span>
                    {line.thinking ? (
                      <span className="text-zinc-600 text-sm italic flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-zinc-600 animate-pulse" />
                        thinking…
                      </span>
                    ) : (
                      <span className="text-zinc-300 text-sm leading-relaxed">
                        {line.decision}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

          {phase === 'generating_report' && (
            <div className="border border-zinc-900 bg-zinc-950 rounded-2xl p-5 flex items-center gap-3">
              <div className="w-4 h-4 border border-zinc-700 border-t-white rounded-full animate-spin" />
              <span className="text-zinc-400 text-sm">
                Synthesizing the alternate timeline narrative and map…
              </span>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </div>
    </main>
  )
}

export default function SimulationPage() {
  return (
    <Suspense>
      <SimulationContent />
    </Suspense>
  )
}
