import asyncio, time, json
from datetime import datetime
from .tools import MockToolRegistry
from .memory import SessionMemory

class DNYFOrchestrator:
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.tools = MockToolRegistry()
        self.memory = SessionMemory()
        self.tasks = {}  # task_id -> {status, logs, result}
    
    async def execute(self, task_id: str, request):
        """Simulated autonomous execution loop"""
        self.tasks[task_id] = {
            "status": "running",
            "goal": request.goal,
            "logs": [],
            "started_at": datetime.now().isoformat(),
            "result": None
        }
        
        await self._log(task_id, "🧠 DNYF TECH initializing...")
        await asyncio.sleep(0.5)
        
        # Phase 1: Planning
        await self._log(task_id, f"🎯 Goal: {request.goal}")
        plan = await self._generate_plan(request.goal)
        await self._log(task_id, f"📋 Plan generated: {len(plan)} steps")
        
        # Phase 2: Execution Loop
        for i, step in enumerate(plan, 1):
            await self._log(task_id, f"🔹 Step {i}/{len(plan)}: {step['action']}")
            
            # Simulate tool call
            tool_result = await self.tools.execute(step['tool'], step['params'])
            await self._log(task_id, f"✅ Tool '{step['tool']}' returned: {tool_result['output'][:100]}...")
            
            # Simulate reflection
            if step.get('test'):
                await self._log(task_id, "🧪 Running validation...")
                await asyncio.sleep(0.3)
                await self._log(task_id, "✅ Validation passed")
            
            await asyncio.sleep(0.4)  # Simulate thinking
        
        # Phase 3: Completion
        self.tasks[task_id]["status"] = "completed"
        self.tasks[task_id]["completed_at"] = datetime.now().isoformat()
        self.tasks[task_id]["result"] = {
            "summary": f"Completed '{request.goal}' with {len(plan)} autonomous steps",
            "files_modified": ["src/auth.py", "tests/test_auth.py"],
            "next_suggestions": ["Add rate limiting", "Write integration tests"]
        }
        await self._log(task_id, "🎉 Task completed successfully!")
    
    async def _generate_plan(self, goal: str) -> list:
        """Mock planner - returns deterministic steps for demo"""
        return [
            {"action": "Analyze project structure", "tool": "filesystem.read", "params": {"path": "."}},
            {"action": "Generate auth module skeleton", "tool": "filesystem.write", "params": {"file": "src/auth.py"}},
            {"action": "Create test file", "tool": "filesystem.write", "params": {"file": "tests/test_auth.py"}},
            {"action": "Run pytest", "tool": "code.execute", "params": {"cmd": "pytest tests/test_auth.py -v"}},
            {"action": "Commit changes", "tool": "git.commit", "params": {"message": "feat: add JWT auth"}}
        ]
    
    async def _log(self, task_id: str, message: str):
        """Append log entry with timestamp"""
        entry = {"ts": datetime.now().isoformat(), "msg": message}
        self.tasks[task_id]["logs"].append(entry)
        # Notify connected websockets (simplified)
    
    def get_status(self, task_id: str):
        return self.tasks.get(task_id, {"error": "Task not found"})
    
    async def stream_logs(self, task_id: str, websocket):
        """Simple log streaming for demo"""
        if task_id not in self.tasks:
            await websocket.send_json({"error": "Task not found"})
            return
        
        # Send existing logs
        for log in self.tasks[task_id]["logs"]:
            await websocket.send_json(log)
            await asyncio.sleep(0.05)
        
        # Keep connection open for new logs (simplified)
        try:
            while self.tasks[task_id]["status"] == "running":
                await asyncio.sleep(0.5)
                for log in self.tasks[task_id]["logs"][-3:]:  # Send recent
                    await websocket.send_json(log)
        except:
            pass
