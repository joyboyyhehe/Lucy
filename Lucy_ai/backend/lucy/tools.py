import inspect
from typing import Any, Dict, List, Type

class LucyTool:
    """Base interface for all Lucy tools.
    Every tool must subclass this and implement run(), name, description, and parameters.
    """
    name: str
    description: str
    parameters: Dict[str, Any]

    async def run(self, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement run()")

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert this tool into the OpenAI/Groq tool specification format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, LucyTool] = {}

    def register(self, tool: LucyTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> LucyTool | None:
        return self._tools.get(name)

    def get_all_tools(self) -> List[LucyTool]:
        return list(self._tools.values())

    def get_groq_schemas(self) -> List[Dict[str, Any]]:
        return [t.to_openai_tool() for t in self.get_all_tools()]

    async def execute(self, name: str, args: Dict[str, Any]) -> Any:
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Tool '{name}' not found."}
        try:
            # Bind arguments to verify matching signature
            sig = inspect.signature(tool.run)
            # Run the tool asynchronously
            result = await tool.run(**args)
            return result
        except Exception as e:
            return {"error": f"Failed to execute tool '{name}': {str(e)}"}

# Instantiate global registry
registry = ToolRegistry()
