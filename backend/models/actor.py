from pydantic import BaseModel, Field


class Actor(BaseModel):
    """A historical figure participating in the simulation."""

    name: str
    role: str
    motivation: str
    influence: int = Field(ge=1, le=10)
    faction: str


class ActorCard(BaseModel):
    """Post-simulation summary card for an actor."""

    name: str
    role: str
    faction: str
    influence: int
    summary: str
