import uuid
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from core.world_builder import generate_actors
from core.simulation import run_simulation
from core.report import generate_report

router = APIRouter(prefix="/simulate", tags=["simulation"])

simulations = {}

class SimulationRequest(BaseModel):
    question: str

class ActorsConfirmRequest(BaseModel):
    simulation_id: str
    actors: list[dict]

@router.post("/init")
def init_simulation(request: SimulationRequest):
    simulation_id = str(uuid.uuid4())
    actors = generate_actors(request.question)
    simulations[simulation_id] = {
        "status": "pending",
        "question": request.question,
        "actors": actors,
        "result": None,
        "report": None
    }
    return {
        "simulation_id": simulation_id,
        "actors": actors
    }

@router.post("/run")
def run(request: ActorsConfirmRequest, background_tasks: BackgroundTasks):
    sim = simulations.get(request.simulation_id)
    if not sim:
        return {"error": "Simulation not found"}
    
    simulations[request.simulation_id]["status"] = "running"
    simulations[request.simulation_id]["actors"] = request.actors

    background_tasks.add_task(run_full_simulation, request.simulation_id)
    return {"status": "running", "simulation_id": request.simulation_id}

def run_full_simulation(simulation_id: str):
    sim = simulations[simulation_id]
    result = run_simulation(sim["question"], sim["actors"], turns=12)
    report = generate_report(result)
    simulations[simulation_id]["status"] = "done"
    simulations[simulation_id]["result"] = result
    simulations[simulation_id]["report"] = report

@router.get("/status/{simulation_id}")
def get_status(simulation_id: str):
    sim = simulations.get(simulation_id)
    if not sim:
        return {"error": "Simulation not found"}
    return {"status": sim["status"]}

@router.get("/report/{simulation_id}")
def get_report(simulation_id: str):
    sim = simulations.get(simulation_id)
    if not sim:
        return {"error": "Simulation not found"}
    if sim["status"] != "done":
        return {"error": "Simulation not ready yet", "status": sim["status"]}
    return sim["report"]