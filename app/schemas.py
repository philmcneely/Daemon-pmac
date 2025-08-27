"""
Pydantic models for request/response validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    is_admin: bool = Field(
        default=False, description="Whether the user should be an admin"
    )


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
    name: str = Field(
        ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    )
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


class MCPJSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


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
    status: Optional[str] = Field(None, pattern=r"^(draft|developing|published)$")
    tags: Optional[List[str]] = None


class SkillData(BaseModel):
    name: str
    category: Optional[str] = None
    level: Optional[str] = Field(
        None, pattern=r"^(beginner|intermediate|advanced|expert)$"
    )
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


class HobbyData(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    skill_level: Optional[str] = Field(
        None, pattern=r"^(beginner|intermediate|advanced)$"
    )
    time_invested: Optional[str] = None
    favorite_aspects: Optional[List[str]] = None


class LookingForData(BaseModel):
    type: str
    description: str
    category: Optional[str] = None
    urgency: Optional[str] = Field(None, pattern=r"^(low|medium|high)$")
    criteria: Optional[str] = None
    contact_method: Optional[str] = None


# Personal API Flexible Markdown Schemas


class PersonalItemMeta(BaseModel):
    """Optional metadata for personal API items"""

    title: Optional[str] = None
    date: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    visibility: Optional[str] = Field(
        default="public", pattern=r"^(public|unlisted|private)$"
    )


class BookItemMeta(PersonalItemMeta):
    """Extended metadata for book items"""

    author: Optional[str] = None
    isbn: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    genres: Optional[List[str]] = None
    date_read: Optional[str] = None


class SkillItemMeta(PersonalItemMeta):
    """Extended metadata for skill items"""

    category: Optional[str] = None
    level: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0)


class PersonalItemCreate(BaseModel):
    """Create/Update request for personal API items"""

    content: str = Field(..., min_length=1, description="Markdown content")
    meta: Optional[PersonalItemMeta] = None


class PersonalItemUpdate(BaseModel):
    """Update request for personal API items"""

    content: Optional[str] = Field(None, min_length=1, description="Markdown content")
    meta: Optional[PersonalItemMeta] = None


class IdeaFlexibleData(BaseModel):
    """Flexible schema for ideas supporting both structured and markdown formats"""

    # New flexible markdown pattern (preferred)
    content: Optional[str] = None
    meta: Optional[PersonalItemMeta] = None

    # Legacy structured pattern (for backward compatibility)
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(draft|developing|published)$")
    tags: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_idea_data(self):
        """Ensure at least content OR title+description is provided"""
        import html

        # Double-unescape HTML for markdown (handles sanitizer double-escaping)
        if self.content:
            # First unescape: sanitizer escaping, second: original entities
            self.content = html.unescape(html.unescape(self.content))
            return self
        elif self.title and self.description:
            # Legacy format - title and description required
            return self
        else:
            raise ValueError(
                "Either 'content' (markdown format) or both 'title' and "
                "'description' (legacy format) must be provided"
            )


class FavoriteBooksFlexibleData(BaseModel):
    """Flexible schema for favorite books supporting structured and markdown formats"""

    # New flexible markdown pattern (preferred)
    content: Optional[str] = None
    meta: Optional[BookItemMeta] = None

    # Legacy structured pattern (for backward compatibility)
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None
    genres: Optional[List[str]] = None
    date_read: Optional[str] = None

    @model_validator(mode="after")
    def validate_book_data(self):
        """Ensure at least content OR title+author is provided"""
        import html

        # Double-unescape HTML for markdown (handles sanitizer double-escaping)
        if self.content:
            # First unescape: sanitizer escaping, second: original entities
            self.content = html.unescape(html.unescape(self.content))
            return self
        elif self.title and self.author:
            # Legacy format - title and author required
            return self
        else:
            raise ValueError(
                "Either 'content' (markdown format) or both 'title' and "
                "'author' (legacy format) must be provided"
            )


class SkillsFlexibleData(BaseModel):
    """Flexible schema for skills supporting structured and markdown formats"""

    # New flexible markdown pattern (preferred)
    content: Optional[str] = None
    meta: Optional[SkillItemMeta] = None

    # Legacy structured pattern (for backward compatibility)
    name: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_skill_data(self):
        """Ensure at least content OR name is provided"""
        import html

        # Double-unescape HTML for markdown (handles sanitizer double-escaping)
        if self.content:
            # First unescape: sanitizer escaping, second: original entities
            self.content = html.unescape(html.unescape(self.content))
            return self
        elif self.name:
            # Legacy format - name required
            return self
        else:
            raise ValueError(
                "Either 'content' (markdown format) or 'name' (legacy format) "
                "must be provided"
            )


class SkillsMatrixData(BaseModel):
    """Schema for skills matrix supporting flexible markdown format"""

    content: str = Field(
        ..., min_length=1, description="Markdown content for skills matrix"
    )
    meta: Optional[PersonalItemMeta] = None

    @model_validator(mode="after")
    def validate_skills_matrix_data(self):
        """Apply HTML unescaping for markdown content"""
        import html

        # Double-unescape HTML for markdown (handles sanitizer double-escaping)
        if self.content:
            # First unescape: sanitizer escaping, second: original entities
            self.content = html.unescape(html.unescape(self.content))
        return self


class ProblemData(BaseModel):
    """Schema for problems supporting flexible markdown format"""

    content: str = Field(
        ..., min_length=1, description="Markdown content for problem description"
    )
    meta: Optional[PersonalItemMeta] = None

    @model_validator(mode="after")
    def validate_problem_data(self):
        """Apply HTML unescaping for markdown content"""
        import html

        # Double-unescape HTML for markdown (handles sanitizer double-escaping)
        if self.content:
            # First unescape: sanitizer escaping, second: original entities
            self.content = html.unescape(html.unescape(self.content))
        return self


# Mapping of endpoint names to their specific models
ENDPOINT_MODELS = {
    "resume": ResumeData,
    "about": AboutData,
    "ideas": IdeaFlexibleData,  # Updated to use flexible model
    "skills": SkillsFlexibleData,  # Updated to use flexible model
    "skills_matrix": SkillsMatrixData,  # Added skills matrix model
    "favorite_books": FavoriteBooksFlexibleData,  # Updated to use flexible model
    "problems": ProblemData,
    "hobbies": HobbyData,
    "looking_for": LookingForData,
}


def get_endpoint_model(endpoint_name: str) -> Optional[Type[BaseModel]]:
    """Get the specific Pydantic model for an endpoint"""
    from typing import cast

    return cast(Optional[Type[BaseModel]], ENDPOINT_MODELS.get(endpoint_name))


class PersonalItemResponse(BaseModel):
    """Response for personal API items"""

    id: str
    content: str
    meta: Optional[PersonalItemMeta] = None
    data: Optional[Dict[str, Any]] = None  # Full data for backward compatibility
    updated_at: datetime
    created_at: datetime


class PersonalItemListResponse(BaseModel):
    """List response for personal API items"""

    items: List[PersonalItemResponse]


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
