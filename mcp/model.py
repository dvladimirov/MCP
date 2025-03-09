from enum import Enum, auto
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ModelCapability(str, Enum):
    """Enum representing the capabilities of a model"""
    COMPLETION = "completion"
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    GIT = "git"
    FILESYSTEM = "filesystem"

class ModelInfo(BaseModel):
    """Represents information about a model in MCP"""
    id: str
    name: str
    description: str
    capabilities: List[ModelCapability]
    context_length: int
    pricing: Dict[str, float] = {}
    metadata: Dict[str, Any] = {} 