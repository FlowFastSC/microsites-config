from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import importlib

app = FastAPI(title="Microsites Tool Runner")

# TEMP: allow all origins during testing; we'll lock this down later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later: restrict to your Framer domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolRequest(BaseModel):
    params: Dict[str, Any] = {}

class ToolResponse(BaseModel):
    ok: bool
    result: Dict[str, Any] | None = None
    error: str | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

def load_tool(site: str):
    """
    Dynamically import sites.<site>.tool and return its `run` function.
    Expect: a callable run(params: dict) -> dict
    """
    try:
        mod = importlib.import_module(f"sites.{site}.tool")
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail=f"Site '{site}' not found")
    if not hasattr(mod, "run") or not callable(getattr(mod, "run")):
        raise HTTPException(status_code=500, detail=f"Tool for '{site}' missing callable run(params)")
    return mod.run

@app.post("/run/{site}", response_model=ToolResponse)
def run_site_tool(site: str, req: ToolRequest):
    try:
        run = load_tool(site)
        result = run(req.params or {})
        if not isinstance(result, dict):
            raise ValueError("Tool must return a dict")
        return ToolResponse(ok=True, result=result)
    except HTTPException:
        raise
    except Exception as e:
        # Keep errors tidy for the client
        raise HTTPException(status_code=400, detail=str(e))
