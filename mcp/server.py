from typing import List, Dict, Optional
from .model import ModelInfo

class MCPServer:
    """Model Control Plane (MCP) Server implementation"""
    
    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
    
    def register_model(self, model: ModelInfo) -> None:
        """Register a model with the MCP server"""
        self._models[model.id] = model
    
    def unregister_model(self, model_id: str) -> bool:
        """Unregister a model from the MCP server"""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get a model by ID"""
        return self._models.get(model_id)
    
    def list_models(self) -> List[ModelInfo]:
        """List all registered models"""
        return list(self._models.values()) 