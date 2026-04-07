#!/usr/bin/env python3
"""
ECI Graph Editor — FastAPI backend

Usage:
    conda run -n edu uvicorn server:app --reload --port 8765
    # OR
    conda run -n edu python server.py

Then open: http://localhost:8765
"""
import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

GRAPH_PATH = Path(__file__).resolve().parent / "eci_graph.json"
STATIC_DIR = Path(__file__).resolve().parent

app = FastAPI(title="ECI Graph Editor", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/graph")
async def get_graph():
    if not GRAPH_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Graph not found: {GRAPH_PATH}")
    with open(GRAPH_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/graph")
async def save_graph(data: dict):
    try:
        with open(GRAPH_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return {"status": "saved", "nodes": len(data.get("nodes", [])), "edges": len(data.get("edges", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files (index.html) — must be mounted last
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    print(f"Graph path: {GRAPH_PATH}")
    print("Open: http://localhost:8765")
    uvicorn.run("server:app", host="0.0.0.0", port=8765, reload=True)
