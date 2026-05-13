import asyncio
import json
import logging
from typing import Any, AsyncIterator

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
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

# Process-local registry of live event buses per simulation. Survives only as
# long as the worker that started the simulation, by design.
_active_buses: dict[str, EventBus] = {}


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
async def run(request: ActorsConfirmRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    sim = storage.get(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    actors = [actor.model_dump() for actor in request.actors]
    storage.update_actors(request.simulation_id, actors, request.turns)
    storage.set_status(request.simulation_id, "running")

    _active_buses[request.simulation_id] = EventBus(asyncio.get_running_loop())

    background_tasks.add_task(_run_full_simulation, request.simulation_id)
    return {"status": "running", "simulation_id": request.simulation_id}


def _run_full_simulation(simulation_id: str) -> None:
    sim = storage.get(simulation_id)
    if sim is None:
        logger.warning("Simulation %s missing at run time", simulation_id)
        return
    bus = _active_buses.get(simulation_id)
    publish = bus.publish if bus else None
    try:
        result = run_simulation(
            sim["question"],
            sim["actors"],
            turns=sim["turns"],
            on_event=publish,
        )
        if bus:
            bus.publish({"type": "report_generating"})
        report = generate_report(result)
        storage.set_result_and_report(simulation_id, result=result, report=report)
        if bus:
            bus.publish({"type": "done", "simulation_id": simulation_id})
    except Exception as exc:
        logger.exception("Simulation %s failed", simulation_id)
        storage.set_status(simulation_id, "error", error=str(exc))
        if bus:
            bus.publish({"type": "error", "error": str(exc)})
    finally:
        if bus:
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
    """Server-Sent Events stream of a running simulation's progress.

    Replays any prior events first, then live-streams as they happen. Closes
    on ``done`` / ``error`` or client disconnect.

    Note: the event bus is process-local. If the backend was restarted after
    the simulation began, this endpoint returns 410 Gone and the client should
    fall back to ``/status`` + ``/report``.
    """
    sim = storage.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    bus = _active_buses.get(simulation_id)
    if bus is None:
        if sim["status"] in ("done", "error"):
            raise HTTPException(status_code=410, detail="Stream closed; fetch /report instead")
        raise HTTPException(status_code=425, detail="Simulation not started in this process")

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
