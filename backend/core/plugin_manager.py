import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Type, Optional
from plugins.base import DNYFPlugin, PluginMetadata

class PluginManager:
    """Discovers, loads, and manages DNYF plugins"""
    
    def __init__(self, plugin_dirs: list[str] = None):
        self.plugin_dirs = plugin_dirs or ["plugins/official", "plugins/community"]
        self.loaded_plugins: Dict[str, DNYFPlugin] = {}
        self.plugin_classes: Dict[str, Type[DNYFPlugin]] = {}
    
    def discover_plugins(self) -> list[PluginMetadata]:
        """Scan plugin directories for available plugins"""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            path = Path(plugin_dir)
            if not path.exists():
                continue
                
            for file in path.glob("*.py"):
                if file.name.startswith("_"):
                    continue
                
                # Import module and find DNYFPlugin subclasses
                module_name = f"{plugin_dir.replace('/', '.')}.{file.stem}"
                try:
                    module = importlib.import_module(module_name)
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (isinstance(obj, type) and 
                            issubclass(obj, DNYFPlugin) and 
                            obj != DNYFPlugin):
                            
                            # Register plugin class
                            plugin_key = obj.metadata.name
                            self.plugin_classes[plugin_key] = obj
                            discovered.append(obj.metadata)
                            
                except Exception as e:
                    print(f"⚠️ Failed to load plugin {file.name}: {e}")
        
        return discovered
    
    def load_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> Optional[DNYFPlugin]:
        """Instantiate and return a plugin instance"""
        plugin_class = self.plugin_classes.get(plugin_name)
        if not plugin_class:
            return None
        
        try:
            instance = plugin_class(config=config)
            self.loaded_plugins[plugin_name] = instance
            return instance
        except Exception as e:
            print(f"❌ Failed to instantiate plugin {plugin_name}: {e}")
            return None
    
    def get_tool_schemas(self) -> list[Dict]:
        """Return combined tool schemas from all loaded plugins"""
        schemas = []
        for plugin in self.loaded_plugins.values():
            try:
                schemas.append(plugin.get_tool_schema())
            except Exception as e:
                print(f"⚠️ Failed to get schema for {plugin.metadata.name}: {e}")
        return schemas
    
    async def execute_plugin_tool(self, tool_name: str, **kwargs) -> Dict:
        """Dispatch tool call to appropriate plugin"""
        # Map tool name to plugin (could be 1:many, handle accordingly)
        for plugin in self.loaded_plugins.values():
            schema = plugin.get_tool_schema()
            if schema["function"]["name"] == tool_name:
                return await plugin.execute(**kwargs)
        
        return {"success": False, "error": f"Unknown plugin tool: {tool_name}"}
    
    async def cleanup_all(self):
        """Call cleanup on all loaded plugins"""
        for plugin in self.loaded_plugins.values():
            try:
                await plugin.cleanup()
            except:
                pass  # Non-critical
