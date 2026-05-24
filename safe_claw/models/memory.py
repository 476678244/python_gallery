"""Memory models for SafeClaw"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from uuid import uuid4


class MemoryLayer(str, Enum):
    """Memory layer types"""
    ACTIVE = "active"
    DORMANT = "dormant"
    DEEP = "deep"
    FORGOTTEN = "forgotten"


class Memory(BaseModel):
    """Base memory model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    layer: MemoryLayer
    created_at: datetime = Field(default_factory=datetime.now)
    accessed_at: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class MemorySearchResult(BaseModel):
    """Memory search result"""
    memory: Memory
    score: float
    match_type: str  # "keyword", "semantic", "context"
