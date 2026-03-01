from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from agent.orchestrator import DNYFOrchestrator
from models.schemas import TaskRequest, AgentResponse
import asyncio, json, uuid

app = FastAPI(title="DNYF TECH Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance (mock mode)
orchestrator = DNYFOrchestrator(mock_mode=True)

@app.post("/api/task")
async def submit_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Submit a new autonomous task to DNYF TECH"""
    task_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(orchestrator.execute, task_id, request)
    return {"task_id": task_id, "status": "queued", "message": "Task accepted"}

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """Poll task progress"""
    return orchestrator.get_status(task_id)

@app.websocket("/ws/logs/{task_id}")
async def websocket_logs(websocket: WebSocket, task_id: str):
    """Real-time agent log streaming"""
    await websocket.accept()
    await orchestrator.stream_logs(task_id, websocket)

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "mock" if orchestrator.mock_mode else "live"}
