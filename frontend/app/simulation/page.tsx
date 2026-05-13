'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { getStatus } from '../lib/api'

const MESSAGES = [
  'Actors are responding to the divergence point...',
  'Bilateral negotiations are taking place...',
  'Unexpected events are being injected...',
  'Influence scores are shaping outcomes...',
  'Historical forces are colliding...',
  'Alliances are forming and breaking...',
  'Decisions are cascading through time...',
  'The alternate timeline is taking shape...',
]

function SimulationContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const simulationId = searchParams.get('id')
  const [messageIndex, setMessageIndex] = useState(0)
  const [dots, setDots] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? '' : d + '.'))
    }, 400)
    return () => clearInterval(dotsInterval)
  }, [])

  useEffect(() => {
    const msgInterval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % MESSAGES.length)
    }, 3000)
    return () => clearInterval(msgInterval)
  }, [])

  useEffect(() => {
    if (!simulationId) return
    let cancelled = false

    const poll = async () => {
      try {
        const data = await getStatus(simulationId)
        if (cancelled) return
        if (data.status === 'done') {
          router.push(`/report?id=${simulationId}`)
          return
        }
        if (data.status === 'error') {
          setError(data.error || 'Simulation failed')
          return
        }
      } catch (err) {
        if (cancelled) return
        console.error(err)
      }
      if (!cancelled) {
        setTimeout(poll, 3000)
      }
    }

    poll()
    return () => {
      cancelled = true
    }
  }, [simulationId, router])

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      <div className="px-6 py-5 border-b border-zinc-900">
        <span className="text-zinc-600 text-sm">Historai</span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="max-w-md w-full space-y-12">

          <div className="flex justify-center">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 border border-zinc-800 rounded-full" />
              <div className="absolute inset-0 border border-t-white rounded-full animate-spin" />
            </div>
          </div>

          <div className="text-center space-y-3">
            <h1 className="text-2xl font-bold">Simulation running{dots}</h1>
            <p className="text-zinc-500 text-sm h-5 transition-all">
              {MESSAGES[messageIndex]}
            </p>
          </div>

          {error ? (
            <div className="border border-rose-900/50 bg-rose-950/30 rounded-2xl p-5 space-y-2">
              <p className="text-[11px] text-rose-400 uppercase tracking-widest">Simulation failed</p>
              <p className="text-rose-200 text-sm">{error}</p>
              <Link href="/" className="inline-block text-xs text-rose-300 hover:text-white transition">
                ← Try again
              </Link>
            </div>
          ) : (
            <div className="border border-zinc-900 rounded-2xl p-5 space-y-3 bg-zinc-950">
              <p className="text-[11px] text-zinc-600 uppercase tracking-widest">What&apos;s happening</p>
              <div className="space-y-2">
                {[
                  'Historical actors make decisions each turn',
                  'High influence actors shape world events',
                  'Random events create unexpected outcomes',
                  'Memory accumulates across turns',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-2">
                    <div className="w-1 h-1 rounded-full bg-zinc-600 mt-2 shrink-0" />
                    <p className="text-zinc-400 text-sm">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-center text-zinc-700 text-xs">
            This usually takes 2–3 minutes
          </p>

        </div>
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
