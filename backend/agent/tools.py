import asyncio, random

class MockToolRegistry:
    """Simulated tools for demo - no real system access"""
    
    TOOLS = {
        "filesystem.read": lambda p: f"📁 Found: {p['path']}/ (mock)",
        "filesystem.write": lambda p: f"✍️  Written: {p['file']} (mock)",
        "code.execute": lambda p: f"🐍 Executed: {p['cmd']}\n✅ 3 passed, 0 failed",
        "git.commit": lambda p: f"🔖 Committed: '{p['message']}' (mock)",
        "safe_shell": lambda p: f"🔧 Ran: {p['cmd']}\nOutput: demo-result-{random.randint(100,999)}"
    }
    
    async def execute(self, tool_name: str, params: dict):
        await asyncio.sleep(0.2)  # Simulate latency
        if tool_name not in self.TOOLS:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            output = self.TOOLS[tool_name](params)
            return {"success": True, "output": output, "tool": tool_name}
        except Exception as e:
            return {"success": False, "error": str(e)}
