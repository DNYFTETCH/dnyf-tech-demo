from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PluginMetadata(BaseModel):
    name: str
    version: str
    author: str
    description: str
    risk_level: str = "medium"  # low/medium/high/critical
    required_permissions: list[str] = Field(default_factory=list)
    config_schema: Optional[Dict] = None  # JSON Schema for plugin config

class DNYFPlugin(ABC):
    """Base class for all DNYF TECH plugins"""
    
    metadata: PluginMetadata
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._validate_config()
    
    def _validate_config(self):
        """Validate plugin config against schema if provided"""
        if self.metadata.config_schema:
            # Use jsonschema to validate self.config
            pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main plugin execution method"""
        pass
    
    @abstractmethod
    def get_tool_schema(self) -> Dict:
        """Return OpenAI-compatible tool schema for LLM"""
        pass
    
    async def cleanup(self):
        """Optional cleanup method called after plugin use"""
        pass

# Example: Docker Plugin
class DockerPlugin(DNYFPlugin):
    metadata = PluginMetadata(
        name="docker",
        version="1.0.0", 
        author="DNYF Team",
        description="Run commands in Docker containers for isolation",
        risk_level="high",
        required_permissions=["docker_daemon_access"],
        config_schema={
            "type": "object",
            "properties": {
                "default_image": {"type": "string", "default": "python:3.11-slim"},
                "network_mode": {"type": "string", "enum": ["none", "bridge"], "default": "none"}
            }
        }
    )
    
    async def execute(self, command: str, image: Optional[str] = None) -> Dict:
        """Run command in isolated Docker container"""
        import docker
        image = image or self.config.get("default_image", "python:3.11-slim")
        
        try:
            client = docker.from_env()
            result = client.containers.run(
                image,
                command,
                remove=True,
                network_mode=self.config.get("network_mode", "none"),
                mem_limit="512m",  # Safety limit
                cpu_quota=50000    # ~50% of one core
            )
            return {"success": True, "output": result.decode()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_tool_schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "docker_execute",
                "description": "Run command in isolated Docker container",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to run"},
                        "image": {"type": "string", "description": "Docker image (optional)"}
                    },
                    "required": ["command"]
                }
            }
        }
