import asyncio
import json
import logging
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.events import SENTINEL, EventBus
from core.report import generate_report
from core.simulation import run_simulation
from core.storage import storage
from core.world_builder import generate_actors
from models.simulation import (
    ActorsConfirmRequest,
    ReportResponse,
    SimulationInitResponse,
    SimulationListResponse,
    SimulationRequest,
    SimulationStatusResponse,
    SimulationSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulate", tags=["simulation"])

# Process-local registry of live event buses per simulation. On serverless
# (Vercel) these only live for the duration of the SSE response that owns them;
# on long-running hosts they persist across the whole simulation lifetime.
_active_buses: dict[str, EventBus] = {}
_active_locks: dict[str, asyncio.Lock] = {}


def _lock_for(simulation_id: str) -> asyncio.Lock:
    lock = _active_locks.get(simulation_id)
    if lock is None:
        lock = asyncio.Lock()
        _active_locks[simulation_id] = lock
    return lock


@router.post("/init", response_model=SimulationInitResponse)
def init_simulation(request: SimulationRequest) -> SimulationInitResponse:
    try:
        actors = generate_actors(request.question)
    except Exception as exc:
        logger.exception("Failed to generate actors")
        raise HTTPException(status_code=502, detail=f"Failed to generate actors: {exc}") from exc

    simulation_id = storage.create(
        question=request.question,
        turns=request.turns,
        actors=actors,
    )
    return SimulationInitResponse(simulation_id=simulation_id, actors=actors)


@router.post("/run")
def run(request: ActorsConfirmRequest) -> dict[str, Any]:
    """Confirm actors and mark the simulation ready. The actual run is driven
    by the SSE ``/stream`` endpoint so we work on serverless hosts too."""
    sim = storage.get(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    actors = [actor.model_dump() for actor in request.actors]
    storage.update_actors(request.simulation_id, actors, request.turns)
    storage.set_status(request.simulation_id, "running")

    return {"status": "running", "simulation_id": request.simulation_id}


async def _simulate_worker(simulation_id: str) -> None:
    sim = storage.get(simulation_id)
    bus = _active_buses.get(simulation_id)
    if sim is None or bus is None:
        return
    try:
        result = await asyncio.to_thread(
            run_simulation,
            sim["question"],
            sim["actors"],
            sim["turns"],
            bus.publish,
        )
        bus.publish({"type": "report_generating"})
        report = await asyncio.to_thread(generate_report, result)
        storage.set_result_and_report(simulation_id, result=result, report=report)
        bus.publish({"type": "done", "simulation_id": simulation_id})
    except Exception as exc:
        logger.exception("Simulation %s failed", simulation_id)
        storage.set_status(simulation_id, "error", error=str(exc))
        bus.publish({"type": "error", "error": str(exc)})
    finally:
        bus.close()


@router.get("/status/{simulation_id}", response_model=SimulationStatusResponse)
def get_status(simulation_id: str) -> SimulationStatusResponse:
    sim = storage.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return SimulationStatusResponse(
        status=sim["status"],
        actors=sim.get("actors", []) or [],
        error=sim.get("error"),
        turns=sim.get("turns"),
    )


@router.get("/list", response_model=SimulationListResponse)
def list_simulations(limit: int = 50) -> SimulationListResponse:
    limit = max(1, min(limit, 200))
    records = storage.list_recent(limit=limit)
    items = [
        SimulationSummary(
            id=r["id"],
            question=r["question"],
            status=r["status"],
            turns=r.get("turns") or 0,
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at"),
            error=r.get("error"),
        )
        for r in records
    ]
    return SimulationListResponse(items=items)


@router.get("/stream/{simulation_id}")
async def stream_simulation(simulation_id: str, request: Request) -> StreamingResponse:
    """Server-Sent Events stream that drives the simulation.

    If the simulation hasn't been started yet (no bus in this process), the
    handler kicks it off inline. This makes it work on serverless hosts where
    BackgroundTasks die with the response.
    """
    sim = storage.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if sim["status"] == "error":
        raise HTTPException(status_code=500, detail=sim.get("error") or "Simulation failed")

    if sim["status"] not in ("running", "done"):
        raise HTTPException(
            status_code=425,
            detail=f"Simulation not ready to stream (status: {sim['status']})",
        )

    lock = _lock_for(simulation_id)
    async with lock:
        bus = _active_buses.get(simulation_id)
        if bus is None and sim["status"] == "running":
            bus = EventBus(asyncio.get_running_loop())
            _active_buses[simulation_id] = bus
            asyncio.create_task(_simulate_worker(simulation_id))
        elif bus is None and sim["status"] == "done":
            raise HTTPException(
                status_code=410,
                detail="Stream closed; fetch /report instead",
            )

    assert bus is not None

    async def event_generator() -> AsyncIterator[bytes]:
        replayed_done = False
        for event in bus.snapshot():
            yield _sse_frame(event)
            if event.get("type") in ("done", "error"):
                replayed_done = True
        if replayed_done or bus.is_closed():
            _cleanup(simulation_id)
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
            if bus.is_closed():
                _cleanup(simulation_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


def _cleanup(simulation_id: str) -> None:
    _active_buses.pop(simulation_id, None)
    _active_locks.pop(simulation_id, None)


def _sse_frame(event: dict[str, Any]) -> bytes:
    event_type = event.get("type", "message")
    data = json.dumps(event, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data}\n\n".encode("utf-8")


@router.get("/report/{simulation_id}", response_model=ReportResponse)
def get_report(simulation_id: str) -> ReportResponse:
    sim = storage.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim["status"] == "error":
        raise HTTPException(status_code=500, detail=sim.get("error") or "Simulation failed")
    if sim["status"] != "done":
        raise HTTPException(
            status_code=425, detail=f"Simulation not ready yet (status: {sim['status']})"
        )

    report = sim["report"]
    result = sim["result"]
    if not report or not result:
        raise HTTPException(status_code=500, detail="Simulation finished without a report")

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
