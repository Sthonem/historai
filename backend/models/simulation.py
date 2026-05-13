from typing import Literal, Optional

from pydantic import BaseModel, Field

from models.actor import Actor, ActorCard


class SimulationRequest(BaseModel):
    question: str
    turns: int = Field(default=6, ge=1, le=20)


class ActorsConfirmRequest(BaseModel):
    simulation_id: str
    actors: list[Actor]
    turns: int = Field(default=6, ge=1, le=20)


class SimulationInitResponse(BaseModel):
    simulation_id: str
    actors: list[Actor]


class SimulationStatusResponse(BaseModel):
    status: Literal["pending", "running", "done", "error"]
    actors: list[Actor] = []
    error: Optional[str] = None
    turns: Optional[int] = None


class TurnEntry(BaseModel):
    turn: int
    event: Optional[str] = None
    decisions: dict[str, str]


class Faction(BaseModel):
    name: str
    color: str
    countries: list[str]


class MapData(BaseModel):
    factions: list[Faction] = []
    year: Optional[str] = None


class ReportResponse(BaseModel):
    question: str
    narrative: str
    actor_cards: list[ActorCard]
    map_data: MapData
    timeline: list[TurnEntry]


class SimulationSummary(BaseModel):
    id: str
    question: str
    status: Literal["pending", "running", "done", "error"]
    turns: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None


class SimulationListResponse(BaseModel):
    items: list[SimulationSummary]
