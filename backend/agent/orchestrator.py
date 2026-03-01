# backend/agent/orchestrator.py (production version)

import asyncio
import json
from datetime import datetime
from integrations.lmstudio_client import LMStudioClient, ToolCall
from agent.tools import RealToolRegistry  # Real implementations below
from agent.memory import HybridMemory

class DNYFOrchestrator:
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.llm = LMStudioClient() if not mock_mode else None
        self.tools = RealToolRegistry() if not mock_mode else MockToolRegistry()
        self.memory = HybridMemory()
        self.tasks = {}
        
        # Define available tools for the LLM
        self.tool_schemas = [
            self.llm.format_tool_schema(
                "read_file",
                "Read contents of a file within project directory",
                {"path": {"type": "string", "description": "Relative path to file"}}
            ) if not mock_mode else {},
            self.llm.format_tool_schema(
                "write_file", 
                "Write content to a file (create or overwrite)",
                {
                    "path": {"type": "string", "description": "Relative path"},
                    "content": {"type": "string", "description": "File content"}
                }
            ) if not mock_mode else {},
            self.llm.format_tool_schema(
                "execute_code",
                "Run Python code in isolated sandbox",
                {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {"type": "integer", "description": "Max seconds (default: 30)"}
                }
            ) if not mock_mode else {},
            self.llm.format_tool_schema(
                "git_commit",
                "Create a git commit with message",
                {"message": {"type": "string", "description": "Commit message"}}
            ) if not mock_mode else {},
        ]
    
    async def execute(self, task_id: str, request):
        """Real autonomous execution loop with LM Studio"""
        self.tasks[task_id] = {            "status": "running",
            "goal": request.goal,
            "logs": [],
            "started_at": datetime.now().isoformat(),
            "result": None,
            "turn_count": 0
        }
        
        await self._log(task_id, "🧠 DNYF TECH initialized with LM Studio")
        
        # Load model if not already loaded
        if not self.mock_mode:
            loaded = await self.llm.load_model(
                "deepseek-r1-distill-qwen-7b@q4_k_m",
                ttl_seconds=3600
            )
            if not loaded:
                await self._log(task_id, "⚠️ Using fallback model")
        
        # Build initial context with project awareness
        context = await self.memory.build_context(request.goal, request.project_path)
        messages = [
            {"role": "system", "content": self._build_system_prompt(request.project_path)},
            {"role": "user", "content": f"Goal: {request.goal}\n\nContext:\n{context}"}
        ]
        
        # Autonomous loop with reflection & tool calling
        max_turns = 15
        for turn in range(max_turns):
            self.tasks[task_id]["turn_count"] = turn + 1
            
            # Get LLM response with tool support
            response_chunks = []
            async for chunk in self.llm.chat_completion(
                messages=messages,
                tools=self.tool_schemas if not self.mock_mode else None,
                stream=True
            ):
                response_chunks.append(chunk)
                # Stream partial content to logs if desired
            
            # Parse response
            final_response = response_chunks[-1] if response_chunks else {}
            assistant_msg = final_response.get("choices", [{}])[0].get("message", {})
            
            # Handle tool calls
            if "tool_calls" in assistant_msg and not self.mock_mode:
                for tool_call in assistant_msg["tool_calls"]:
                    await self._handle_tool_call(task_id, tool_call, messages)
                continue  # Continue loop with tool results appended            
            # Check for completion
            if self._is_task_complete(assistant_msg.get("content", "")):
                break
            
            # Append to conversation history
            messages.append({"role": "assistant", "content": assistant_msg.get("content")})
            
            # Self-reflection checkpoint every 5 turns
            if turn > 0 and turn % 5 == 0:
                await self._reflect_and_adjust(task_id, messages, request.goal)
        
        # Finalize task
        self.tasks[task_id]["status"] = "completed"
        self.tasks[task_id]["completed_at"] = datetime.now().isoformat()
        self.tasks[task_id]["result"] = await self._generate_summary(task_id, request.goal)
        await self._log(task_id, "🎉 Task completed successfully!")
        
        # Auto-unload model to free resources
        if not self.mock_mode:
            await self.llm.unload_model()
    
    async def _handle_tool_call(self, task_id: str, tool_call: Dict, messages: List):
        """Execute a tool called by the LLM and feed result back"""
        tool_id = tool_call["id"]
        tool_name = tool_call["function"]["name"]
        tool_args = json.loads(tool_call["function"]["arguments"])
        
        await self._log(task_id, f"🔧 Executing tool: {tool_name}({tool_args})")
        
        try:
            # Execute real tool
            result = await self.tools.execute(tool_name, tool_args)
            
            # Log result (truncate long outputs)
            output_preview = result.get("output", "")[:200] + ("..." if len(result.get("output","")) > 200 else "")
            await self._log(task_id, f"✅ {tool_name} returned: {output_preview}")
            
            # Append tool response to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": json.dumps(result) if isinstance(result, dict) else str(result)
            })
            
        except Exception as e:
            error_msg = f"❌ Tool error: {str(e)}"
            await self._log(task_id, error_msg)
            messages.append({
                "role": "tool",                "tool_call_id": tool_id,
                "content": json.dumps({"error": str(e)})
            })
    
    def _build_system_prompt(self, project_path: str) -> str:
        return f"""You are DNYF TECH, an autonomous coding agent running offline via LM Studio.

## Rules
- Work only within project directory: {project_path}
- Never execute destructive commands (rm -rf, sudo, curl|bash)
- Always validate changes with tests before committing
- Output concise, actionable responses
- Use tools for all file/system operations

## Available Tools
- read_file(path): Read file contents
- write_file(path, content): Create/overwrite file  
- execute_code(code, timeout): Run Python in sandbox
- git_commit(message): Commit changes with message

## Output Format
- Plan first, then execute step-by-step
- After each tool call, assess result before proceeding
- When done, summarize changes and suggest next steps

Stay focused. Be efficient. Ship quality code."""
    
    # ... [additional helper methods: _log, _is_task_complete, _reflect_and_adjust, _generate_summary]
