export interface Actor {
  name: string
  role: string
  motivation: string
  influence: number
  faction: string
}

export interface ActorCard {
  name: string
  role: string
  faction: string
  influence: number
  summary: string
}

export interface Faction {
  name: string
  color: string
  countries: string[]
}

export interface MapData {
  factions: Faction[]
  year?: string | null
}

export interface TimelineTurn {
  turn: number
  event?: string | null
  decisions: Record<string, string>
}

export interface Report {
  question: string
  narrative: string
  actor_cards: ActorCard[]
  map_data: MapData
  timeline: TimelineTurn[]
}

export type SimulationStatus = 'pending' | 'running' | 'done' | 'error'

export interface SimulationStatusPayload {
  status: SimulationStatus
  actors: Actor[]
  error?: string | null
  turns?: number | null
}

export interface SimulationInitPayload {
  simulation_id: string
  actors: Actor[]
}
