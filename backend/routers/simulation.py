import asyncio
import json
import logging
import uuid
from typing import Any, AsyncIterator

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.events import SENTINEL, EventBus
from core.report import generate_report
from core.simulation import run_simulation
from core.world_builder import generate_actors
from models.simulation import (
    ActorsConfirmRequest,
    ReportResponse,
    SimulationInitResponse,
    SimulationRequest,
    SimulationStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulate", tags=["simulation"])

simulations: dict[str, dict[str, Any]] = {}


@router.post("/init", response_model=SimulationInitResponse)
def init_simulation(request: SimulationRequest) -> SimulationInitResponse:
    simulation_id = str(uuid.uuid4())
    try:
        actors = generate_actors(request.question)
    except Exception as exc:
        logger.exception("Failed to generate actors")
        raise HTTPException(status_code=502, detail=f"Failed to generate actors: {exc}") from exc

    simulations[simulation_id] = {
        "status": "pending",
        "question": request.question,
        "actors": actors,
        "turns": request.turns,
        "result": None,
        "report": None,
        "error": None,
        "bus": None,
    }
    return SimulationInitResponse(simulation_id=simulation_id, actors=actors)


@router.post("/run")
async def run(request: ActorsConfirmRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    sim = simulations.get(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim["status"] = "running"
    sim["actors"] = [actor.model_dump() for actor in request.actors]
    sim["turns"] = request.turns
    sim["bus"] = EventBus(asyncio.get_running_loop())

    background_tasks.add_task(_run_full_simulation, request.simulation_id)
    return {"status": "running", "simulation_id": request.simulation_id}


def _run_full_simulation(simulation_id: str) -> None:
    sim = simulations[simulation_id]
    bus: EventBus = sim["bus"]
    try:
        result = run_simulation(
            sim["question"],
            sim["actors"],
            turns=sim["turns"],
            on_event=bus.publish,
        )
        bus.publish({"type": "report_generating"})
        report = generate_report(result)
        sim["result"] = result
        sim["report"] = report
        sim["status"] = "done"
        bus.publish({"type": "done", "simulation_id": simulation_id})
    except Exception as exc:
        logger.exception("Simulation %s failed", simulation_id)
        sim["status"] = "error"
        sim["error"] = str(exc)
        bus.publish({"type": "error", "error": str(exc)})
    finally:
        bus.close()


@router.get("/status/{simulation_id}", response_model=SimulationStatusResponse)
def get_status(simulation_id: str) -> SimulationStatusResponse:
    sim = simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return SimulationStatusResponse(
        status=sim["status"],
        actors=sim.get("actors", []),
        error=sim.get("error"),
        turns=sim.get("turns"),
    )


@router.get("/stream/{simulation_id}")
async def stream_simulation(simulation_id: str, request: Request) -> StreamingResponse:
    """Server-Sent Events stream of a running simulation's progress.

    Replays any prior events first, then live-streams as they happen.
    Closes when the simulation reaches ``done`` or ``error``.
    """
    sim = simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    bus: EventBus | None = sim.get("bus")
    if bus is None:
        raise HTTPException(status_code=425, detail="Simulation not started yet")

    async def event_generator() -> AsyncIterator[bytes]:
        replayed_done = False
        for event in bus.snapshot():
            yield _sse_frame(event)
            if event.get("type") in ("done", "error"):
                replayed_done = True
        if replayed_done or bus.is_closed():
            return

        queue = bus.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield b": keepalive\n\n"
                    continue
                if event is SENTINEL:
                    break
                yield _sse_frame(event)  # type: ignore[arg-type]
                if isinstance(event, dict) and event.get("type") in ("done", "error"):
                    break
        finally:
            bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_frame(event: dict[str, Any]) -> bytes:
    event_type = event.get("type", "message")
    data = json.dumps(event, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data}\n\n".encode("utf-8")


@router.get("/report/{simulation_id}", response_model=ReportResponse)
def get_report(simulation_id: str) -> ReportResponse:
    sim = simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim["status"] == "error":
        raise HTTPException(status_code=500, detail=sim.get("error") or "Simulation failed")
    if sim["status"] != "done":
        raise HTTPException(status_code=425, detail=f"Simulation not ready yet (status: {sim['status']})")

    report = sim["report"]
    result = sim["result"]

    timeline: list[dict[str, Any]] = []
    for turn in result["turns"]:
        decisions = {
            actor_name: (decision[:150] + "..." if len(decision) > 150 else decision)
            for actor_name, decision in turn["decisions"].items()
        }
        timeline.append(
            {
                "turn": turn["turn"],
                "event": turn.get("event"),
                "decisions": decisions,
            }
        )

    return ReportResponse(
        question=report["question"],
        narrative=report["narrative"],
        actor_cards=report["actor_cards"],
        map_data=report["map_data"],
        timeline=timeline,
    )
