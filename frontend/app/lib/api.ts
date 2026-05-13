import type {
  Actor,
  Report,
  SimulationInitPayload,
  SimulationListPayload,
  SimulationStatusPayload,
} from './types'

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(detail, res.status)
  }
  return res.json() as Promise<T>
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

export function initSimulation(
  question: string,
  turns: number,
): Promise<SimulationInitPayload> {
  return request<SimulationInitPayload>('/simulate/init', {
    method: 'POST',
    body: JSON.stringify({ question, turns }),
  })
}

export function runSimulation(
  simulationId: string,
  actors: Actor[],
  turns: number,
): Promise<{ status: string; simulation_id: string }> {
  return request('/simulate/run', {
    method: 'POST',
    body: JSON.stringify({ simulation_id: simulationId, actors, turns }),
  })
}

export function getStatus(simulationId: string): Promise<SimulationStatusPayload> {
  return request<SimulationStatusPayload>(`/simulate/status/${simulationId}`)
}

export function getReport(simulationId: string): Promise<Report> {
  return request<Report>(`/simulate/report/${simulationId}`)
}

export function listSimulations(limit = 50): Promise<SimulationListPayload> {
  return request<SimulationListPayload>(`/simulate/list?limit=${limit}`)
}

export function streamUrl(simulationId: string): string {
  return `${API_BASE_URL}/simulate/stream/${simulationId}`
}
