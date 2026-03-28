from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Historai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Historai API is running"}

from core.llm import llm_call

@app.get("/test-llm")
def test_llm():
    result = llm_call("In one sentence, what would have happened if the Ottoman Empire had not entered World War I?")
    return {"result": result}

from core.world_builder import generate_actors

@app.get("/test-actors")
def test_actors():
    actors = generate_actors("What if the Ottoman Empire had not entered World War I?")
    return {"actors": actors}

from core.simulation import run_simulation

@app.get("/test-simulation")
def test_simulation():
    actors = generate_actors("What if the Ottoman Empire had not entered World War I?")
    result = run_simulation(
        question="What if the Ottoman Empire had not entered World War I?",
        actors=actors,
        turns=3
    )
    return {"turns": len(result["turns"]), "first_turn": result["turns"][0]}

from core.report import generate_report

@app.get("/test-report")
def test_report():
    actors = generate_actors("What if the Ottoman Empire had not entered World War I?")
    simulation = run_simulation(
        question="What if the Ottoman Empire had not entered World War I?",
        actors=actors,
        turns=3
    )
    report = generate_report(simulation)
    return report

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.simulation import router as simulation_router

load_dotenv()

app = FastAPI(title="Historai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router)

@app.get("/")
def root():
    return {"status": "Historai API is running"}