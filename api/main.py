import os
import asyncio
import json
import uuid
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import sys
sys.path.append('..')

# Import your existing application
from app import run_query
from research_transparency.types import AppState
from api.database import ResearchDatabase, ResearchSessionRecord

app = FastAPI(title="Research Agent API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database instance
db = ResearchDatabase()

# In-memory storage for active sessions
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
    # Create session in database
    research_id = db.create_session(request.query, request.depth)

    # Initialize in-memory session for real-time tracking
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
                extras={"depth": request.depth},
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

                # Update database with progress
                db_update = {}
                if step_result.get("intent"):
                    db_update["intent"] = step_result["intent"]
                if step_result.get("research_plan"):
                    db_update["research_plan"] = _serialize_research_plan(step_result["research_plan"])
                if step_result.get("reasoning_log"):
                    db_update["execution_log"] = _serialize_reasoning_log(step_result["reasoning_log"])

                if db_update:
                    db.update_session(research_id, **db_update)

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
            final_state = research_sessions[research_id]["state"]

            # Save final results to database
            final_response = final_state.get("final_response", "")
            sources = []  # TODO: Extract sources from final_state if available
            db.complete_session(research_id, final_response, sources)

            # Send final completion update
            if research_id in active_connections:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(send_completion_update(research_id, final_state))
                    loop.close()
                except Exception as e:
                    print(f"Failed to send completion update: {e}")

        except Exception as e:
            research_sessions[research_id]["status"] = "failed"
            research_sessions[research_id]["error"] = str(e)

            # Update database with failure
            db.update_session(research_id, status="failed")

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

# Dashboard API endpoints
@app.get("/api/dashboard/sessions")
async def get_recent_sessions(limit: int = 20):
    """Get recent research sessions for dashboard"""
    try:
        sessions = db.get_recent_sessions(limit)
        return {
            "sessions": [
                {
                    "id": session.id,
                    "query": session.query,
                    "depth": session.depth,
                    "intent": session.intent,
                    "status": session.status,
                    "created_at": session.created_at,
                    "completed_at": session.completed_at,
                    "duration_seconds": session.duration_seconds,
                    "final_response_preview": session.final_response[:200] + "..." if session.final_response and len(session.final_response) > 200 else session.final_response
                }
                for session in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/session/{session_id}")
async def get_session_details(session_id: str):
    """Get full details of a specific session"""
    try:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Parse JSON fields
        research_plan = json.loads(session.research_plan) if session.research_plan else None
        execution_log = json.loads(session.execution_log) if session.execution_log else None
        sources = json.loads(session.sources) if session.sources else None

        return {
            "id": session.id,
            "query": session.query,
            "depth": session.depth,
            "intent": session.intent,
            "status": session.status,
            "research_plan": research_plan,
            "execution_log": execution_log,
            "final_response": session.final_response,
            "sources": sources,
            "created_at": session.created_at,
            "completed_at": session.completed_at,
            "duration_seconds": session.duration_seconds
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/search")
async def search_sessions(q: str, limit: int = 20):
    """Search research sessions"""
    try:
        sessions = db.search_sessions(q, limit)
        return {
            "sessions": [
                {
                    "id": session.id,
                    "query": session.query,
                    "depth": session.depth,
                    "intent": session.intent,
                    "status": session.status,
                    "created_at": session.created_at,
                    "completed_at": session.completed_at,
                    "duration_seconds": session.duration_seconds,
                    "final_response_preview": session.final_response[:200] + "..." if session.final_response and len(session.final_response) > 200 else session.final_response
                }
                for session in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        return db.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/dashboard/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a research session"""
    try:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # For now, we'll just mark as deleted (you could add a deleted flag to schema)
        # Or implement actual deletion
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("DELETE FROM research_sessions WHERE id = ?", (session_id,))

        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Research Agent API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)