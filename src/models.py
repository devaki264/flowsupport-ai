# src/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class QueryCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    PRODUCT = "product"
    ACCOUNT = "account"
    GENERAL = "general"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DocumentChunk(BaseModel):
    """Structured document chunk with metadata"""
    text: str = Field(..., min_length=10)
    source: str
    page: int = Field(..., gt=0)
    chunk_id: int = Field(..., ge=0)
    category: Optional[QueryCategory] = None
    
    class Config:
        use_enum_values = True

class RetrievedDocument(BaseModel):
    """Document retrieved from vector store"""
    content: str
    source: str
    page: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    
    @validator('relevance_score')
    def score_precision(cls, v):
        return round(v, 3)

class EscalationDecision(BaseModel):
    """Structured escalation decision"""
    should_escalate: bool
    reason: str
    category: QueryCategory
    priority: Literal["low", "medium", "high", "urgent"]
    suggested_team: Optional[str] = None

class AgentResponse(BaseModel):
    """Complete agent response with metadata"""
    query: str
    response: str
    escalation: EscalationDecision
    retrieved_docs: List[RetrievedDocument]
    confidence: ConfidenceLevel
    avg_relevance_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
