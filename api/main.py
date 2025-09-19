import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import sys
sys.path.append('..')

# Import your existing application
from app import run_query
from research_transparency.types import AppState

app = FastAPI(title="Research Agent API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (use Redis in production)
research_sessions: Dict[str, Dict[str, Any]] = {}
active_connections: Dict[str, WebSocket] = {}

class ResearchQuery(BaseModel):
    query: str
    depth: str = "standard"

class ResearchResponse(BaseModel):
    research_id: str
    status: str
    message: str

@app.post("/api/research", response_model=ResearchResponse)
async def create_research_query(request: ResearchQuery):
    """Start a new research query"""
    research_id = str(uuid.uuid4())

    # Initialize session
    research_sessions[research_id] = {
        "query": request.query,
        "depth": request.depth,
        "status": "started",
        "created_at": datetime.now().isoformat(),
        "state": None,
        "progress": []
    }

    # Start research in background thread
    def run_research():
        try:
            # Import here to avoid circular imports
            from app import create_app
            from research_transparency.types import AppState

            app = create_app()

            # Create initial state
            initial_state = AppState(
                query=request.query,
                intent="unknown",
                confidence=0.0,
                extras={},
                processed=False,
                search_query="",
                search_results=[],
                final_response="",
                research_plan=None,
                task_progress={},
                reasoning_log=[],
                intermediate_results={},
                research_progress=None,
                research_bundle=None,
                is_research_complete=False,
                current_stage_description="",
                user_visible_progress=""
            )

            # Stream the workflow execution with progress updates
            for step_result in app.stream(initial_state, stream_mode="values"):
                # Update session state with partial results
                research_sessions[research_id]["state"] = step_result

                # Send immediate WebSocket update
                if research_id in active_connections:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(send_progress_update(research_id, step_result))
                        loop.close()
                    except Exception as e:
                        print(f"Failed to send progress update: {e}")

            # Mark as completed
            research_sessions[research_id]["status"] = "completed"

            # Send final completion update
            if research_id in active_connections:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(send_completion_update(research_id, research_sessions[research_id]["state"]))
                    loop.close()
                except Exception as e:
                    print(f"Failed to send completion update: {e}")

        except Exception as e:
            research_sessions[research_id]["status"] = "failed"
            research_sessions[research_id]["error"] = str(e)
            print(f"Research error: {e}")

    thread = threading.Thread(target=run_research)
    thread.daemon = True
    thread.start()

    return ResearchResponse(
        research_id=research_id,
        status="started",
        message="Research query initiated"
    )

@app.get("/api/research/{research_id}")
async def get_research_status(research_id: str):
    """Get current status of research query"""
    if research_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Research session not found")

    session = research_sessions[research_id]
    return {
        "research_id": research_id,
        "status": session["status"],
        "query": session["query"],
        "created_at": session["created_at"],
        "state": session.get("state"),
        "error": session.get("error")
    }

@app.websocket("/ws/research/{research_id}")
async def websocket_endpoint(websocket: WebSocket, research_id: str):
    """WebSocket endpoint for real-time research progress"""
    await websocket.accept()
    active_connections[research_id] = websocket

    try:
        # Send initial status
        if research_id in research_sessions:
            session = research_sessions[research_id]
            await websocket.send_text(json.dumps({
                "type": "status",
                "research_id": research_id,
                "status": session["status"],
                "query": session["query"]
            }))

        # Keep connection alive and send updates
        while True:
            if research_id in research_sessions:
                session = research_sessions[research_id]

                # Send progress updates
                if session.get("state"):
                    state = session["state"]
                    progress_data = {
                        "type": "progress",
                        "research_id": research_id,
                        "status": session["status"],
                        "data": {
                            "query": state.get("query"),
                            "intent": state.get("intent"),
                            "confidence": state.get("confidence"),
                            "research_plan": _serialize_research_plan(state.get("research_plan")),
                            "reasoning_log": _serialize_reasoning_log(state.get("reasoning_log", [])),
                            "research_progress": _serialize_research_progress(state.get("research_progress")),
                            "final_response": state.get("final_response"),
                            "processed": state.get("processed", False)
                        }
                    }
                    await websocket.send_text(json.dumps(progress_data))

                # Break if completed
                if session["status"] in ["completed", "failed"]:
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        if research_id in active_connections:
            del active_connections[research_id]

def _serialize_research_plan(research_plan):
    """Convert research plan to JSON-serializable format"""
    if not research_plan:
        return None

    return {
        "rationale": research_plan.rationale,
        "estimated_duration": research_plan.estimated_duration,
        "tasks": [
            {
                "id": task.id,
                "description": task.description,
                "rationale": task.rationale,
                "status": task.status
            } for task in research_plan.tasks
        ]
    }

def _serialize_reasoning_log(reasoning_log):
    """Convert reasoning log to JSON-serializable format"""
    return [
        {
            "timestamp": step.timestamp.isoformat(),
            "stage": step.stage,
            "reasoning": step.reasoning,
            "task_id": step.task_id
        } for step in reasoning_log
    ]

def _serialize_research_progress(research_progress):
    """Convert research progress to JSON-serializable format"""
    if not research_progress:
        return None

    return {
        "current_stage": research_progress.current_stage,
        "current_reasoning": research_progress.current_reasoning,
        "tasks_completed": research_progress.tasks_completed,
        "total_tasks": research_progress.total_tasks,
        "facts_collected": research_progress.facts_collected,
        "sources_processed": research_progress.sources_processed,
        "confidence_score": research_progress.confidence_score
    }

async def send_progress_update(research_id: str, state):
    """Send progress update via WebSocket"""
    if research_id in active_connections:
        ws = active_connections[research_id]
        try:
            progress_data = {
                "type": "progress",
                "research_id": research_id,
                "status": "in_progress",
                "data": {
                    "query": state.get("query"),
                    "intent": state.get("intent"),
                    "confidence": state.get("confidence"),
                    "research_plan": _serialize_research_plan(state.get("research_plan")),
                    "reasoning_log": _serialize_reasoning_log(state.get("reasoning_log", [])),
                    "research_progress": _serialize_research_progress(state.get("research_progress")),
                    "final_response": state.get("final_response"),
                    "processed": state.get("processed", False)
                }
            }
            await ws.send_text(json.dumps(progress_data))
            print(f"Sent progress update for {research_id}")
        except Exception as e:
            print(f"Failed to send progress update: {e}")

async def send_completion_update(research_id: str, state):
    """Send completion update via WebSocket"""
    if research_id in active_connections:
        ws = active_connections[research_id]
        try:
            completion_data = {
                "type": "status",
                "research_id": research_id,
                "status": "completed",
                "data": {
                    "query": state.get("query"),
                    "intent": state.get("intent"),
                    "confidence": state.get("confidence"),
                    "research_plan": _serialize_research_plan(state.get("research_plan")),
                    "reasoning_log": _serialize_reasoning_log(state.get("reasoning_log", [])),
                    "research_progress": _serialize_research_progress(state.get("research_progress")),
                    "final_response": state.get("final_response"),
                    "processed": state.get("processed", False)
                }
            }
            await ws.send_text(json.dumps(completion_data))
            print(f"Sent completion update for {research_id}")
        except Exception as e:
            print(f"Failed to send completion update: {e}")

@app.get("/")
async def root():
    return {"message": "Research Agent API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)