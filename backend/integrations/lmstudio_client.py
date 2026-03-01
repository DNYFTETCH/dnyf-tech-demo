import httpx
import json
from typing import AsyncGenerator, Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LMStudioConfig(BaseModel):
    base_url: str = "http://localhost:1234/v1"
    model_id: str = "deepseek-r1-distill-qwen-7b"
    context_length: int = 8192
    temperature: float = 0.1  # Low for deterministic tool-calling
    max_tokens: int = 4096
    timeout: int = 120

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]

class LMStudioClient:
    """Production-ready client for LM Studio's OpenAI-compatible API"""
    
    def __init__(self, config: Optional[LMStudioConfig] = None):
        self.config = config or LMStudioConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={"Content-Type": "application/json"}
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict, None]:
        """
        Send chat request with optional tool-calling support.
        Yields streaming chunks if stream=True.
        """
        payload = {
            "model": self.config.model_id,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"  # Let model decide when to call tools        
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            
            if stream:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            yield chunk
                        except json.JSONDecodeError:
                            continue
            else:
                result = await response.aread()
                yield json.loads(result)
    
    async def load_model(self, model_key: str, ttl_seconds: int = 1800) -> bool:
        """JIT-load a model into LM Studio with auto-evict TTL"""
        try:
            await self.client.post("/models/load", json={
                "model_key": model_key,
                "ttl": ttl_seconds,  # Auto-unload after idle
                "context_length": self.config.context_length
            })
            self.config.model_id = model_key.split("/")[-1]  # Extract short name
            return True
        except httpx.HTTPError as e:
            print(f"❌ Model load failed: {e}")
            return False
    
    async def unload_model(self) -> bool:
        """Free VRAM by unloading current model"""
        try:
            await self.client.post("/models/unload")
            return True
        except:
            return False
    
    def format_tool_schema(self, name: str, description: str, parameters: Dict) -> Dict:
        """Helper to format tools for OpenAI-compatible schema"""
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",                    "properties": parameters,
                    "required": list(parameters.keys())
                }
            }
        }
    
    async def close(self):
        await self.client.aclose()
