"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


class EndpointBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    description: Optional[str] = None
    endpoint_schema: Dict[str, Any] = Field(..., alias="schema")
    is_public: bool = True


class EndpointCreate(EndpointBase):
    pass


class EndpointUpdate(BaseModel):
    description: Optional[str] = None
    endpoint_schema: Optional[Dict[str, Any]] = Field(None, alias="schema")
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class EndpointResponse(EndpointBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class DataEntryBase(BaseModel):
    data: Dict[str, Any]


class DataEntryCreate(DataEntryBase):
    pass


class DataEntryUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DataEntryResponse(DataEntryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    endpoint_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    key: str  # Only returned on creation
    expires_at: Optional[datetime] = None
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: bool
    uptime_seconds: float


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime


# MCP (Model Context Protocol) Models
class MCPToolResponse(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


class MCPToolCallResponse(BaseModel):
    content: List[Dict[str, Any]]
    is_error: bool = False


# Endpoint-specific models for better validation
class ResumeData(BaseModel):
    name: str
    title: str
    summary: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    skills: Optional[Dict[str, List[str]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    awards: Optional[List[str]] = None
    volunteer: Optional[List[Union[str, Dict[str, Any]]]] = None
    updated_at: Optional[str] = None


class AboutData(BaseModel):
    name: str
    title: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


class IdeaData(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r'^(draft|developing|published)$')
    tags: Optional[List[str]] = None


class SkillData(BaseModel):
    name: str
    category: Optional[str] = None
    level: Optional[str] = Field(None, pattern=r'^(beginner|intermediate|advanced|expert)$')
    years_experience: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None


class BookData(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None
    genres: Optional[List[str]] = None
    date_read: Optional[str] = None  # ISO date string


class ProblemData(BaseModel):
    title: str
    description: str
    domain: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r'^(identifying|researching|solving|solved)$')
    priority: Optional[str] = Field(None, pattern=r'^(low|medium|high|critical)$')
    approach: Optional[str] = None


class HobbyData(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    skill_level: Optional[str] = Field(None, pattern=r'^(beginner|intermediate|advanced)$')
    time_invested: Optional[str] = None
    favorite_aspects: Optional[List[str]] = None


class LookingForData(BaseModel):
    type: str
    description: str
    category: Optional[str] = None
    urgency: Optional[str] = Field(None, pattern=r'^(low|medium|high)$')
    criteria: Optional[str] = None
    contact_method: Optional[str] = None


# Mapping of endpoint names to their specific models
ENDPOINT_MODELS = {
    "resume": ResumeData,
    "about": AboutData,
    "ideas": IdeaData,
    "skills": SkillData,
    "favorite_books": BookData,
    "problems": ProblemData,
    "hobbies": HobbyData,
    "looking_for": LookingForData,
}


def get_endpoint_model(endpoint_name: str) -> Optional[BaseModel]:
    """Get the specific Pydantic model for an endpoint"""
    return ENDPOINT_MODELS.get(endpoint_name)


# Generic response models
class PaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    size: int
    pages: int


class BulkOperationResponse(BaseModel):
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = []


class BackupResponse(BaseModel):
    filename: str
    size_bytes: int
    created_at: datetime
