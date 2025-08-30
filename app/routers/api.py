"""
Module: routers.api
Description: Core API routes for dynamic endpoints, user data management,
             and adaptive single/multi-user routing

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- fastapi: 0.104.1+ - API routing and request/response handling
- sqlalchemy: 2.0+ - Database operations and queries
- pydantic: 2.5.2+ - Data validation and serialization

Usage:
    # Routes are automatically included in main FastAPI app
    # Supports both single-user and multi-user endpoint patterns:

    # Single-user mode (≤1 user):
    # GET /api/v1/resume
    # POST /api/v1/ideas

    # Multi-user mode (2+ users):
    # GET /api/v1/resume/users/pmac
    # POST /api/v1/ideas/users/pmac

Notes:
    - Automatically detects single vs multi-user mode
    - Dynamic endpoint creation and management
    - Privacy filtering applied to all public endpoints
    - Comprehensive data import/export functionality
    - Audit logging for all data modifications
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, cast

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..auth import (
    get_current_active_user,
    get_current_admin_user,
    get_password_hash,
    get_user_from_api_key,
)
from ..database import AuditLog, DataEntry, Endpoint, User, UserPrivacySettings, get_db
from ..schemas import (
    DataEntryCreate,
    DataEntryResponse,
    DataEntryUpdate,
    EndpointResponse,
    EndpointUpdate,
    PaginatedResponse,
    PersonalItemListResponse,
    PersonalItemResponse,
    UserCreate,
    get_endpoint_model,
)
from ..security import SecurityError, validate_user_route_security
from ..utils import mask_sensitive_data, sanitize_data_dict, validate_url

router = APIRouter(
    prefix="/api/v1", tags=["📊 Content API - Adaptive Multi-User System"]
)


def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT or API key, but don't require authentication"""
    from ..auth import verify_token

    # Try API key first
    user = get_user_from_api_key(request, db)
    if user:
        return user

    # Try JWT token from Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            # Verify the JWT token (without raising exceptions)
            from jose import JWTError, jwt

            from ..config import settings
            from ..schemas import TokenData

            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            username: Optional[str] = payload.get("sub")
            if username:
                user = db.query(User).filter(User.username == username).first()
                if user and user.is_active:
                    return user
        except (JWTError, Exception):
            # Invalid token, but this is optional auth, so continue
            pass

    # No valid authentication found
    return None


def log_audit_action(
    db: Session,
    action: str,
    table_name: str,
    record_id: int,
    user: Optional[User] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    request: Optional[Request] = None,
):
    """Log an audit action"""
    audit_log = AuditLog(
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        user_id=user.id if user else None,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(audit_log)


# Dynamic endpoint routes
@router.get(
    "/endpoints",
    response_model=List[EndpointResponse],
    summary="List all available endpoints",
    description="""
    **Get a complete list of all available endpoints in the system**

    This returns all available endpoints with their current schema definitions.

    ### 📊 Core Endpoints (Available by default)

    - **resume** - Professional resume and work history (structured schema)
    - **skills** - Technical and soft skills with proficiency levels (content/meta)
    - **ideas** - Ideas, thoughts, and concepts (content/meta)
    - **favorite_books** - Book recommendations and reviews (content/meta)
    - **hobbies** - Hobbies and personal interests (content/meta)
    - **problems** - Problems you're working on or have solved (content/meta)
    - **looking_for** - Things you're currently seeking (content/meta)
    - **about** - Basic personal/entity information (content/meta)

    ### 📝 Schema Types

    **Content/Meta Schema**: Most endpoints use a flexible content + metadata pattern:
    ```json
    {
      "content": "Markdown content (required)",
      "meta": {
        "title": "Optional title",
        "date": "Optional date",
        "tags": ["optional", "tags"],
        "status": "Optional status",
        "visibility": "public|unlisted|private"
      }
    }
    ```

    **Structured Schema**: Resume endpoint uses a fixed structure with specific fields.

    ### 🎯 Dynamic Endpoints

    All endpoints are configurable via the database. Admins can modify schemas
    and add new endpoints. Each endpoint can have its own validation schema
    and be public or private.

    ### 🔗 Using Endpoints

    Once you have the endpoint names, you can:
    - **GET** `/api/v1/{endpoint_name}` - Get data
    - **POST** `/api/v1/{endpoint_name}` - Add data (auth required)
    - **PUT** `/api/v1/{endpoint_name}/{id}` - Update data (auth required)
    - **DELETE** `/api/v1/{endpoint_name}/{id}` - Delete data (auth required)

    In multi-user mode, use: `/api/v1/{endpoint_name}/users/{username}`
    """,
    responses={
        200: {
            "description": "List of all available endpoints",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "resume",
                            "description": "Professional resume and work history",
                            "schema": {
                                "name": {"type": "string", "required": True},
                                "title": {"type": "string", "required": True},
                                "contact": {"type": "object"},
                                "experience": {"type": "array"},
                                "education": {"type": "array"},
                            },
                            "is_public": True,
                            "is_active": True,
                            "created_at": "2024-08-24T10:00:00Z",
                        },
                        {
                            "id": 2,
                            "name": "skills",
                            "description": "Technical and soft skills",
                            "schema": {
                                "name": {"type": "string", "required": True},
                                "level": {
                                    "type": "string",
                                    "enum": [
                                        "beginner",
                                        "intermediate",
                                        "advanced",
                                        "expert",
                                    ],
                                },
                                "category": {"type": "string"},
                                "years_experience": {"type": "integer"},
                            },
                            "is_public": True,
                            "is_active": True,
                            "created_at": "2024-08-24T10:00:00Z",
                        },
                    ]
                }
            },
        }
    },
)
async def list_endpoints(
    active_only: bool = Query(
        True, description="Only return active (non-deleted) endpoints"
    ),
    db: Session = Depends(get_db),
):
    """List all available endpoints"""
    query = db.query(Endpoint)
    if active_only:
        query = query.filter(Endpoint.is_active == True)

    endpoints = query.all()
    return endpoints


@router.get("/endpoints/{endpoint_name}", response_model=EndpointResponse)
async def get_endpoint(endpoint_name: str, db: Session = Depends(get_db)):
    """Retrieve endpoint configuration and schema by name.

    Fetches the configuration details for a specific endpoint including
    its schema definition, description, and active status.

    Args:
        endpoint_name (str): Name of the endpoint to retrieve.
        db (Session): Database session dependency.

    Returns:
        Endpoint: Endpoint configuration object with schema and metadata.

    Raises:
        HTTPException: 404 if endpoint not found or inactive.

    Note:
        - Only returns active endpoints (is_active=True)
        - Includes full JSON schema for data validation
        - Used for endpoint discovery and schema introspection
    """
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    return endpoint


@router.get(
    "/system/info",
    response_model=Dict[str, Any],
    summary="Get system information",
    description="""
    **Get comprehensive system information and endpoint routing patterns**

    This endpoint helps you understand how the API currently operates based
    on the number of users.

    ### 🔄 Adaptive Routing Information

    The response tells you:
    - **Current mode**: `single_user` or `multi_user`
    - **Endpoint patterns**: How to access endpoints in the current mode
    - **Available endpoints**: List of all accessible endpoints
    - **User information**: Current users in the system

    ### 📊 Use Cases

    - **API Discovery**: Find out what endpoints are available
    - **Mode Detection**: Understand if you need user-specific URLs
    - **Integration**: Build clients that adapt to single/multi-user modes
    - **Debugging**: Troubleshoot endpoint access issues

    ### 🎯 Example Responses

    **Single User Mode** (1 user or less):
    ```json
    {
      "mode": "single_user",
      "endpoint_pattern": "/api/v1/{endpoint_name}",
      "available_endpoints": [...],
      "users": ["admin"]
    }
    ```

    **Multi-User Mode** (2+ users):
    ```json
    {
      "mode": "multi_user",
      "endpoint_pattern": "/api/v1/{endpoint_name}/users/{username}",
      "available_endpoints": [...],
      "users": ["admin", "john", "jane"]
    }
    ```
    """,
    responses={
        200: {
            "description": "System information and routing patterns",
            "content": {
                "application/json": {
                    "examples": {
                        "single_user_mode": {
                            "summary": "Single user mode response",
                            "value": {
                                "mode": "single_user",
                                "total_users": 1,
                                "users": ["admin"],
                                "endpoint_pattern": "/api/v1/{endpoint_name}",
                                "example_urls": [
                                    "/api/v1/resume",
                                    "/api/v1/skills",
                                    "/api/v1/ideas",
                                ],
                                "available_endpoints": [
                                    {
                                        "name": "resume",
                                        "description": (
                                            "Professional resume and work history"
                                        ),
                                    },
                                    {
                                        "name": "skills",
                                        "description": "Technical and soft skills",
                                    },
                                    {
                                        "name": "ideas",
                                        "description": "Ideas and thoughts",
                                    },
                                ],
                                "total_endpoints": 8,
                            },
                        },
                        "multi_user_mode": {
                            "summary": "Multi-user mode response",
                            "value": {
                                "mode": "multi_user",
                                "total_users": 3,
                                "users": ["admin", "john", "jane"],
                                "endpoint_pattern": (
                                    "/api/v1/{endpoint_name}/users/{username}"
                                ),
                                "example_urls": [
                                    "/api/v1/resume/users/john",
                                    "/api/v1/skills/users/jane",
                                    "/api/v1/ideas/users/admin",
                                ],
                                "available_endpoints": [
                                    {
                                        "name": "resume",
                                        "description": (
                                            "Professional resume and work history"
                                        ),
                                    },
                                    {
                                        "name": "skills",
                                        "description": "Technical and soft skills",
                                    },
                                    {
                                        "name": "ideas",
                                        "description": "Ideas and thoughts",
                                    },
                                ],
                                "total_endpoints": 8,
                            },
                        },
                    }
                }
            },
        }
    },
)
async def get_system_info(db: Session = Depends(get_db)):
    """Retrieve comprehensive system information and endpoint metadata.

    Provides detailed information about the API system including available
    endpoints, routing patterns, adaptive endpoint configurations, and
    system status information.

    Args:
        db (Session): Database session dependency.

    Returns:
        Dict[str, Any]: System information including:
            - adaptive_endpoints: Dynamic endpoint configuration details
            - endpoint_routing: Available endpoint routing patterns
            - total_endpoints: Count of active endpoints
            - system_metadata: API version and capabilities

    Note:
        - Includes only active endpoints in the response
        - Provides adaptive endpoint configuration details
        - Used for API discovery and client configuration
        - Returns comprehensive metadata for system introspection
    """
    adaptive_info = get_adaptive_endpoint_info(db)

    # Get available endpoints
    endpoints = (
        db.query(Endpoint)
        .filter(Endpoint.is_active == True, Endpoint.is_public == True)
        .all()
    )

    endpoint_list = [
        {"name": ep.name, "description": ep.description} for ep in endpoints
    ]

    return {
        **adaptive_info,
        "available_endpoints": endpoint_list,
        "total_endpoints": len(endpoint_list),
    }


# Universal endpoint routing - adapts between single and multi-user modes
@router.get(
    "/{endpoint_name}/users/{username}",
    response_model=List[Dict[str, Any]],
    summary="Get Public User Content (Clean View)",
    description="""
    **Get clean, user-friendly content without internal management IDs**

    This is the **public endpoint** for content consumption. Perfect for displaying
    content to visitors, embedding in websites, or API consumers who don't need
    to manage content.

    ### 📖 Content Consumption vs Management

    **This endpoint (Public/Clean View)**:
    ```
    GET /api/v1/about/users/blackbeard
    → Clean content WITHOUT item IDs
    → No authentication required
    → Returns: [{"content": "...", "meta": {...}}]
    → Perfect for: websites, public APIs, content display
    ```

    **Management endpoint (Authenticated)**:
    ```
    GET /api/v1/about (with JWT token)
    → Content WITH item IDs for management
    → Authentication required
    → Returns: {"items": [{"id": "42", "content": "...", ...}]}
    → Perfect for: content creators, editing, updates
    ```

    ### 🔄 Adaptive Behavior

    **Single User Mode (≤1 user)**: Redirects to simple endpoints
    ```
    /api/v1/about/users/john → redirects to → /api/v1/about
    ```

    **Multi-User Mode (2+ users)**: Direct access
    ```
    /api/v1/about/users/john → works directly
    /api/v1/skills/users/jane → works directly
    ```

    ### 🔐 Privacy Filtering

    Automatically applies privacy filtering based on user settings:
    - **business_card**: Minimal networking info
    - **professional**: Work-appropriate details
    - **public_full**: Full public information (default)
    - **ai_safe**: Safe for AI assistant access

    ### 📊 Response Format

    Returns clean content without internal IDs:
    ```json
    [
      {
        "content": "# About Me\\n\\nI am a software developer...",
        "meta": {
          "title": "About John Doe",
          "date": "2025-08-27",
          "tags": ["biography", "personal"],
          "status": "active",
          "visibility": "public"
        }
      }
    ]
    ```

    No `id` field - this is for content consumption, not management.
    """,
)
async def get_specific_user_data_universal(
    endpoint_name: str,
    username: str,
    request: Request,
    level: str = Query(
        "public_full",
        description="Privacy level: business_card, professional, public_full, ai_safe",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(True, description="Filter active items only"),
    db: Session = Depends(get_db),
):
    """
    **Public endpoint for clean content display without management IDs**

    Perfect for content consumption - no authentication required.
    For content management (with item IDs), use the authenticated endpoint instead.
    """
    from ..privacy import get_privacy_filter
    from ..utils import is_single_user_mode

    # SECURITY: Validate endpoint_name and username for path traversal and injection
    try:
        validate_user_route_security(username, endpoint_name)
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Additional check for any non-alphanumeric characters except underscore and hyphen
    import re

    if not re.match(r"^[a-zA-Z0-9_-]+$", endpoint_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint name contains invalid characters",
        )

    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username contains invalid characters",
        )

    # In single-user mode, redirect to the simple endpoint
    if is_single_user_mode(db):
        # Preserve query parameters in redirect
        query_string = str(request.url.query) if request.url.query else ""
        location = f"/api/v1/{endpoint_name}"
        if query_string:
            location += f"?{query_string}"

        raise HTTPException(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            detail=f"In single-user mode, use /api/v1/{endpoint_name} instead",
            headers={"Location": location},
        )

    # Find the user
    user = (
        db.query(User).filter(User.username == username, User.is_active == True).first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found"
        )

    # Check AI assistant access permission
    if level == "ai_safe":
        privacy_settings = (
            db.query(UserPrivacySettings)
            .filter(UserPrivacySettings.user_id == user.id)
            .first()
        )
        if privacy_settings and not privacy_settings.ai_assistant_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="AI assistant access not permitted for this user",
            )

    # Find endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    # Only allow access to public endpoints
    if not endpoint.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is not publicly accessible",
        )

    # Query user's data
    query = db.query(DataEntry).filter(
        DataEntry.endpoint_id == endpoint.id, DataEntry.created_by_id == user.id
    )

    if active_only:
        query = query.filter(DataEntry.is_active == True)

    # Pagination
    offset = (page - 1) * size
    data_entries = query.offset(offset).limit(size).all()

    # Apply privacy filtering
    privacy_filter = get_privacy_filter(db, user)
    filtered_data = []

    for entry in data_entries:
        # Check visibility in data.meta first - skip private/unlisted items
        entry_data: dict[str, Any] = (
            entry.data if entry.data and isinstance(entry.data, dict) else {}
        )
        entry_meta = entry_data.get("meta", {})
        entry_visibility = entry_meta.get("visibility", "public")

        # Skip private and unlisted items for public endpoints
        if entry_visibility in ["private", "unlisted"]:
            continue

        filtered_entry = privacy_filter.filter_data(
            cast(Dict[str, Any], entry.data),
            privacy_level=level,
            is_authenticated=False,
        )
        if filtered_entry:
            # Apply additional sensitive data masking
            masked_entry = mask_sensitive_data(filtered_entry, level)
            filtered_data.append(masked_entry)

    # If no visible content found, return appropriate message
    if not filtered_data:
        return JSONResponse(
            status_code=200,
            content={
                "message": "No visible content available for this user",
                "timestamp": datetime.now().isoformat(),
            },
        )

    return filtered_data


# Create adaptive routing helper
def get_adaptive_endpoint_info(db: Session) -> Dict[str, Any]:
    """Get information about how endpoints should be accessed based on user count"""
    from ..utils import get_single_user, is_single_user_mode

    single_user_mode = is_single_user_mode(db)

    if single_user_mode:
        single_user = get_single_user(db)
        return {
            "mode": "single_user",
            "user": single_user.username if single_user else None,
            "user_info": (
                {
                    "username": single_user.username,
                    "full_name": single_user.full_name,
                    "email": single_user.email,
                }
                if single_user
                else None
            ),
            "endpoint_pattern": "/api/v1/{endpoint_name}",
            "example": "/api/v1/resume",
        }
    else:
        users = db.query(User).filter(User.is_active == True).all()
        return {
            "mode": "multi_user",
            "users": [
                {
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                }
                for user in users
            ],
            "endpoint_pattern": "/api/v1/{endpoint_name}/users/{username}",
            "example": "/api/v1/resume/users/john",
            "privacy_levels": [
                "business_card",
                "professional",
                "public_full",
                "ai_safe",
            ],
        }


def filter_sensitive_data(
    data: dict,
    is_authenticated: bool = False,
    user: Optional[User] = None,
    db: Optional[Session] = None,
) -> dict:
    """
    Legacy wrapper for the new privacy filtering system
    Maintains backward compatibility while using enhanced filtering
    """
    if db and user:
        from ..privacy import get_privacy_filter

        privacy_filter = get_privacy_filter(db, user)
        return privacy_filter.filter_data(
            data, privacy_level="public_full", is_authenticated=is_authenticated
        )
    else:
        # Fallback to basic filtering if no user context
        if db is None:
            # Return data with minimal pattern-based filtering when no db available
            return {
                k: v
                for k, v in data.items()
                if not any(
                    pattern in k.lower()
                    for pattern in ["password", "secret", "token", "key"]
                )
            }

        from ..privacy import PrivacyFilter

        basic_filter = PrivacyFilter(db, None)
        return basic_filter._apply_sensitive_patterns(data)


# Data management for endpoints
@router.get(
    "/{endpoint_name}",
    response_model=PersonalItemListResponse,
    summary="Get Content with Management IDs (Authenticated)",
    description="""
    **Get content data with item IDs for content management**

    This endpoint shows content with internal item IDs needed for content management
    operations (create, update, delete). Perfect for content creators and editors.

    ### 📝 Content Management Workflow

    **This endpoint is part of the content management workflow:**
    1. **Login**: `/auth/login` → Get JWT token
    2. **List Content**: `GET /api/v1/{endpoint}` (this endpoint) → Get item IDs
    3. **Update**: `PUT /api/v1/{endpoint}/{item_id}` → Update specific content
    4. **Delete**: `DELETE /api/v1/{endpoint}/{item_id}` → Remove content

    ### 🔄 Two Endpoint Types

    **Authenticated (Management View)** - This endpoint:
    ```
    GET /api/v1/about
    → Shows content WITH item IDs for management
    → Requires JWT authentication
    → Returns: {"items": [{"id": "42", "content": "...", ...}]}
    ```

    **Public (Clean View)** - For consumers:
    ```
    GET /api/v1/about/users/{username}
    → Shows clean content WITHOUT item IDs
    → No authentication required
    → Returns: [{"content": "...", "meta": {...}}]
    ```

    ### 🔐 Authentication Required

    This endpoint requires JWT authentication. Include token in Authorization header:
    ```
    Authorization: Bearer <your_jwt_token>
    ```

    ### 📊 Available Content Endpoints

    **Content/Meta Schema** (Flexible markdown content):
    - **about** - Personal/entity information
    - **ideas** - Ideas and thoughts
    - **skills** - Skills and competencies
    - **projects** - Personal and professional projects
    - **values** - Personal values and principles
    - **goals** - Personal and professional goals
    - **learning** - Current learning activities
    - And many more...

    **Structured Schema**:
    - **resume** - Professional resume (structured format)

    ### 🔐 Privacy Levels

    - **business_card**: Minimal networking info
    - **professional**: Work-appropriate details
    - **public_full**: Full public information
    - **ai_safe**: AI-assistant safe (no sensitive data)

    ### 📊 Response Format

    Returns content with item IDs for management:
    ```json
    {
      "items": [
        {
          "id": "42",
          "content": "# My Content\\n\\nMarkdown content here...",
          "meta": {
            "title": "Content Title",
            "date": "2025-08-27",
            "tags": ["tag1", "tag2"],
            "visibility": "public"
          },
          "data": { /* full content structure */ },
          "created_at": "2025-08-27T10:30:00Z",
          "updated_at": "2025-08-27T15:45:00Z"
        }
      ],
      "total": 1,
      "page": 1,
      "size": 50
    }
    ```

    The `id` field is what you need for update/delete operations.
    """,
    responses={
        200: {
            "description": "List of data entries for the endpoint",
            "content": {
                "application/json": {
                    "examples": {
                        "resume_data": {
                            "summary": "Resume endpoint response",
                            "value": [
                                {
                                    "id": 1,
                                    "name": "John Doe",
                                    "title": "Software Engineer",
                                    "contact": {
                                        "email": "john@example.com",
                                        "location": "San Francisco, CA",
                                    },
                                    "experience": [
                                        {
                                            "company": "Tech Corp",
                                            "position": "Senior Developer",
                                            "duration": "2020-2024",
                                        }
                                    ],
                                    "created_at": "2024-08-24T10:30:00Z",
                                }
                            ],
                        },
                        "skills_data": {
                            "summary": "Skills endpoint response",
                            "value": [
                                {
                                    "id": 1,
                                    "name": "Python Programming",
                                    "category": "Programming Languages",
                                    "level": "expert",
                                    "years_experience": 8,
                                    "description": "Expert in Python development",
                                }
                            ],
                        },
                        "ideas_data": {
                            "summary": "Ideas endpoint response",
                            "value": [
                                {
                                    "id": 1,
                                    "title": "AI-Powered Code Review",
                                    "description": (
                                        "Automated code review using machine learning"
                                    ),
                                    "category": "technology",
                                    "status": "concept",
                                }
                            ],
                        },
                    }
                }
            },
        },
        404: {"description": "Endpoint not found"},
    },
)
async def get_endpoint_data(
    endpoint_name: str,
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    active_only: bool = Query(
        True, description="Only return active (non-deleted) items"
    ),
    privacy_level: Optional[str] = Query(
        None,
        description="Privacy filtering level",
        enum=["business_card", "professional", "public_full", "ai_safe"],
    ),
    level: Optional[str] = Query(
        None,
        description="Privacy level alias (same as privacy_level)",
        enum=["business_card", "professional", "public_full", "ai_safe"],
    ),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get data for a specific endpoint"""
    from ..utils import get_single_user, is_single_user_mode

    # SECURITY: Enhanced validation for endpoint_name
    try:
        from ..security import validate_endpoint_route_security

        validate_endpoint_route_security(endpoint_name)
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Handle level parameter as alias for privacy_level (for redirect compatibility)
    if level and privacy_level is None:
        privacy_level = level

    # Find endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    # Check if endpoint is public or user has access
    if not endpoint.is_public and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this endpoint",
        )

    # Query data with adaptive user filtering
    query = db.query(DataEntry).filter(DataEntry.endpoint_id == endpoint.id)
    if active_only:
        query = query.filter(DataEntry.is_active == True)

    # SECURITY FIX: Proper user filtering for both single and multi-user modes
    if is_single_user_mode(db):
        # FIXED: In single-user mode, only return data for the single active user
        single_user = get_single_user(db)
        if single_user:
            # STRICT SECURITY: Only return data created by the single user
            # Do NOT include orphaned data (created_by_id = NULL)
            query = query.filter(DataEntry.created_by_id == single_user.id)
        else:
            # No users in system - return empty result
            query = query.filter(DataEntry.id == -1)  # No results
    else:
        if current_user:
            query = query.filter(
                (DataEntry.created_by_id == current_user.id)
                | (DataEntry.created_by_id.is_(None))
            )
        else:
            # In multi-user mode without authentication, check if data exists
            total_entries = (
                db.query(DataEntry).filter(DataEntry.endpoint_id == endpoint.id).count()
            )
            if total_entries > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Multi-user mode: User-specific endpoint required",
                        "message": (
                            f"This system has multiple users. To access "
                            f"{endpoint_name} data, use the user-specific "
                            f"endpoint format:"
                        ),
                        "pattern": f"/api/v1/{endpoint_name}/users/{{username}}",
                        "example": f"/api/v1/{endpoint_name}/users/your_username",
                        "note": (
                            "Replace 'your_username' with the actual username. "
                            "Alternatively, authenticate to access your own data."
                        ),
                    },
                )
            query = query.filter(DataEntry.created_by_id.is_(None))

    # Pagination
    offset = (page - 1) * size
    data_entries = query.offset(offset).limit(size).all()

    # Apply visibility filtering for unauthenticated users (including single-user mode)
    if not current_user:
        visible_entries = []
        for entry in data_entries:
            entry_data = cast(Dict[str, Any], entry.data)
            meta = entry_data.get("meta", {})
            visibility = meta.get("visibility", "public")
            if visibility == "public":
                visible_entries.append(entry)
        data_entries = visible_entries

    # Apply privacy filtering based on privacy_level parameter or authentication status
    should_apply_privacy = privacy_level is not None or (
        not current_user and not is_single_user_mode(db)
    )

    items = []
    for entry in data_entries:
        # Privacy filtering and masking
        data: Dict[str, Any] = cast(Dict[str, Any], entry.data)
        if should_apply_privacy:
            if privacy_level is None:
                privacy_level = "public_full"
            if entry.created_by_id:
                entry_user = (
                    db.query(User).filter(User.id == entry.created_by_id).first()
                )
                if entry_user:
                    from ..privacy import get_privacy_filter

                    privacy_filter = get_privacy_filter(db, entry_user)
                    filtered_data = privacy_filter.filter_data(
                        cast(Dict[str, Any], data), privacy_level=privacy_level
                    )
                    data = filtered_data.get("data", filtered_data)
            else:
                from ..privacy import get_privacy_filter

                privacy_filter = get_privacy_filter(db)
                filtered_data = privacy_filter.filter_data(
                    cast(Dict[str, Any], data),
                    privacy_level=privacy_level,
                    is_authenticated=current_user is not None,
                )
                data = filtered_data
            data = mask_sensitive_data(data, privacy_level)
        else:
            data = mask_sensitive_data(data, "public_full")

        # Extract content and meta for flexible markdown endpoints
        content = data.get("content") if isinstance(data, dict) else None
        meta = data.get("meta") if isinstance(data, dict) else None

        # Handle updated_at field - use created_at if updated_at is None
        updated_at: datetime = cast(datetime, entry.created_at)
        if hasattr(entry, "updated_at") and entry.updated_at is not None:
            updated_at = cast(datetime, entry.updated_at)

        item = PersonalItemResponse(
            id=str(entry.id),
            content=content if content is not None else "",
            meta=meta,
            data=data if isinstance(data, dict) else {},
            updated_at=updated_at,
            created_at=cast(datetime, entry.created_at),
        )
        items.append(item)

    return PersonalItemListResponse(items=items)


@router.post(
    "/{endpoint_name}",
    response_model=Dict[str, Any],
    summary="Add data to endpoint",
    description="""
    **Add new data to any endpoint (authentication required)**

    This endpoint allows you to add data to any endpoint in the system:
    - **Core endpoints**: resume, skills, ideas, favorite_books, hobbies,
      problems, looking_for, about
    - **Dynamic endpoints**: All endpoints support content/meta or structured schemas

    ### 🔄 Adaptive Behavior

    **Single User Mode**: Data is automatically assigned to the single user
    **Multi-User Mode**: Data is assigned to the authenticated user

    ### 📝 Data Validation

    Each endpoint has its own schema validation:
    - **resume**: Requires `name` and `title`, supports contact, experience,
      education, skills, etc.
    - **skills**: Requires `name`, supports category, level
      (beginner/intermediate/advanced/expert), years_experience
    - **ideas**: Requires `title` and `description`, supports category,
      status
    - **favorite_books**: Requires `title` and `author`, supports rating
      (1-5), review, genres
    - **hobbies**: Supports name, category, description, years_active
    - **problems**: Supports title, description, category, status
    - **looking_for**: Supports title, description, category, urgency
    - **about**: Free-form personal information

    ### 💡 Examples

    Try adding data to different endpoints with the request body examples below.
    """,
    responses={
        200: {
            "description": "Data successfully added",
            "content": {
                "application/json": {
                    "examples": {
                        "resume_response": {
                            "summary": "Resume data added",
                            "value": {
                                "id": 123,
                                "message": "Data added to resume",
                                "data": {
                                    "name": "John Doe",
                                    "title": "Software Engineer",
                                    "contact": {"email": "john@example.com"},
                                },
                            },
                        },
                        "skill_response": {
                            "summary": "Skill data added",
                            "value": {
                                "id": 124,
                                "message": "Data added to skills",
                                "data": {
                                    "name": "Python Programming",
                                    "level": "expert",
                                    "years_experience": 8,
                                },
                            },
                        },
                        "idea_response": {
                            "summary": "Idea data added",
                            "value": {
                                "id": 125,
                                "message": "Data added to ideas",
                                "data": {
                                    "title": "AI Code Review Tool",
                                    "description": (
                                        "Automated code review using machine learning"
                                    ),
                                    "category": "technology",
                                },
                            },
                        },
                    }
                }
            },
        },
        400: {"description": "Validation error - check required fields"},
        401: {"description": "Authentication required"},
        404: {"description": "Endpoint not found"},
    },
)
async def add_endpoint_data(
    endpoint_name: str,
    data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add data to an endpoint (authenticated users only)"""
    from ..utils import get_single_user, is_single_user_mode

    # Find endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    # Adaptive user assignment
    user_id = None
    if is_single_user_mode(db):
        # Single-user mode: assign to the single user or leave as system data
        single_user = get_single_user(db)
        user_id = single_user.id if single_user else None
    else:
        # Multi-user mode: always assign to current user
        user_id = current_user.id

    # Auto-generate meta field if missing
    if "meta" not in data or data["meta"] is None:
        from datetime import datetime

        data["meta"] = {
            "title": data.get("meta", {}).get("title", ""),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": [],
            "visibility": "public",
        }
    elif isinstance(data["meta"], dict):
        # Ensure required meta fields have defaults
        meta = data["meta"]
        if "visibility" not in meta:
            meta["visibility"] = "public"
        if "date" not in meta:
            from datetime import datetime

            meta["date"] = datetime.now().strftime("%Y-%m-%d")
        if "tags" not in meta:
            meta["tags"] = []
        if "title" not in meta:
            meta["title"] = ""

    # Sanitize input
    sanitized_data = sanitize_data_dict(data)

    # Validate data against endpoint schema if we have a specific model
    endpoint_model: Optional[Type[BaseModel]] = get_endpoint_model(endpoint_name)
    if endpoint_model:
        try:
            validated_data = endpoint_model(**sanitized_data)
            sanitized_data = validated_data.model_dump(exclude_unset=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data validation error: {str(e)}",
            )

    # Create data entry
    data_entry = DataEntry(
        endpoint_id=endpoint.id,
        data=sanitized_data,
        created_by_id=user_id,  # Use adaptive user assignment
    )
    db.add(data_entry)
    db.commit()
    db.refresh(data_entry)

    # Log audit action
    log_audit_action(
        db,
        "CREATE",
        "data_entries",
        cast(int, data_entry.id),
        current_user,
        None,
        sanitized_data,
        request,
    )
    db.commit()

    # Include ownership information in response
    response = {
        "id": data_entry.id,
        "message": f"Data added to {endpoint_name}",
        "data": data_entry.data,
    }

    # Add created_by information if available
    if data_entry.created_by:
        response["created_by"] = data_entry.created_by.username

    return response


@router.get("/{endpoint_name}/{item_id}", response_model=Dict[str, Any])
async def get_endpoint_item(
    endpoint_name: str,
    item_id: str,  # Changed to str to validate before conversion
    privacy_level: Optional[str] = Query(
        None,
        description="Privacy filtering level",
        enum=["business_card", "professional", "public_full", "ai_safe"],
    ),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get a single item from an endpoint"""
    from ..utils import get_single_user, is_single_user_mode

    # SECURITY: Validate endpoint_name for security issues
    try:
        from ..security import InputValidator, validate_endpoint_route_security

        validate_endpoint_route_security(endpoint_name)
        # Validate item_id for dangerous patterns
        InputValidator.validate_input_security(item_id, "item_id")
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Validate item_id: must be a positive integer
    try:
        item_id_int = int(item_id)
        if item_id_int <= 0:
            raise ValueError("Item ID must be positive")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item ID must be a positive integer",
        )

    # Find endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    # Check if endpoint is public or user has access
    if not endpoint.is_public and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this endpoint",
        )

    # Find the specific data entry
    query = db.query(DataEntry).filter(
        DataEntry.endpoint_id == endpoint.id,
        DataEntry.id == item_id_int,  # Use the validated integer
        DataEntry.is_active == True,
    )

    # SECURITY FIX: Proper user filtering for both single and multi-user modes
    if is_single_user_mode(db):
        # FIXED: In single-user mode, only return data for the single active user
        single_user = get_single_user(db)
        if single_user:
            # STRICT SECURITY: Only return data created by the single user
            # Do NOT include orphaned data (created_by_id = NULL)
            query = query.filter(DataEntry.created_by_id == single_user.id)
        else:
            # No users in system - return empty result
            query = query.filter(DataEntry.id == -1)  # No results
    else:
        # Multi-user mode: filter by user ownership
        if current_user:
            query = query.filter(DataEntry.created_by_id == current_user.id)
        else:
            # Public access in multi-user mode - only show public data
            # Note: We'll handle public visibility through endpoint configuration
            pass  # For now, allow access but apply privacy filtering later

    data_entry = query.first()

    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id_int} not found in endpoint '{endpoint_name}'",
        )

    # Apply privacy filtering
    data: Dict[str, Any] = cast(Dict[str, Any], data_entry.data)

    # Check meta.visibility for unauthenticated users
    if not current_user:
        meta = data.get("meta", {})
        visibility = meta.get("visibility", "public")
        if visibility in ["private", "unlisted"]:
            return JSONResponse(
                status_code=200, content={"message": "No visible content available"}
            )

    if privacy_level:
        # Apply masking based on privacy level
        data = mask_sensitive_data(data, privacy_level)

    # Return item with ID and data fields merged for backward compatibility
    result = {"id": data_entry.id}
    result.update(data)
    return result


@router.put(
    "/{endpoint_name}/{item_id}",
    response_model=Dict[str, Any],
    summary="Update Content Item",
    description="Update specific content using item ID (requires authentication)",
)
async def update_endpoint_data(
    endpoint_name: str,
    item_id: int,
    data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update specific content item by ID (authenticated users only).

    **Content Management Workflow:**
    1. Login via `/auth/login` to get JWT token
    2. Find item ID via authenticated GET `/api/v1/{endpoint_name}`
    3. Update content using this endpoint with the item ID

    **Request Body:**
    ```json
    {
      "content": "# Updated Markdown Content\\n\\nYour updated content here...",
      "meta": {
        "title": "Updated Title",
        "date": "2025-08-27",
        "tags": ["tag1", "tag2"],
        "status": "active",
        "visibility": "public"
      }
    }
    ```

    **Security:**
    - Requires valid JWT token in Authorization header
    - Users can only update their own content (unless admin)
    - All updates are logged in audit trail

    **Example:**
    ```bash
    curl -X PUT "/api/v1/about/42" \\
         -H "Authorization: Bearer <token>" \\
         -H "Content-Type: application/json" \\
         -d '{"content": "Updated content...", "meta": {...}}'
    ```
    """
    # Find endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    # Find data entry
    data_entry = (
        db.query(DataEntry)
        .filter(DataEntry.id == item_id, DataEntry.endpoint_id == endpoint.id)
        .first()
    )

    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found in {endpoint_name}",
        )

    # Check ownership - users can only modify their own data unless they're admin
    if not current_user.is_admin and data_entry.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own data",
        )

    # Store old data for audit
    old_data = cast(Dict[str, Any], data_entry.data).copy()

    # Auto-generate meta field if missing
    if "meta" not in data or data["meta"] is None:
        from datetime import datetime

        data["meta"] = {
            "title": data.get("meta", {}).get("title", ""),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": [],
            "visibility": "public",
        }
    elif isinstance(data["meta"], dict):
        # Ensure required meta fields have defaults
        meta = data["meta"]
        if "visibility" not in meta:
            meta["visibility"] = "public"
        if "date" not in meta:
            from datetime import datetime

            meta["date"] = datetime.now().strftime("%Y-%m-%d")
        if "tags" not in meta:
            meta["tags"] = []
        if "title" not in meta:
            meta["title"] = ""

    # Sanitize and validate new data
    sanitized_data = sanitize_data_dict(data)
    endpoint_model: Optional[Type[BaseModel]] = get_endpoint_model(endpoint_name)
    if endpoint_model:
        try:
            validated_data = endpoint_model(**sanitized_data)
            sanitized_data = validated_data.model_dump(exclude_unset=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data validation error: {str(e)}",
            )

    # Update data entry
    data_entry.data = cast(Any, sanitized_data)
    db.commit()

    # Log audit action
    log_audit_action(
        db,
        "UPDATE",
        "data_entries",
        cast(int, data_entry.id),
        current_user,
        old_data,
        sanitized_data,
        request,
    )
    db.commit()

    return {
        "id": data_entry.id,
        "message": f"Data updated in {endpoint_name}",
        "data": data_entry.data,
    }


@router.delete("/{endpoint_name}/{item_id}")
async def delete_endpoint_data(
    endpoint_name: str,
    item_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete data from an endpoint (authenticated users only)"""
    # Find endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    # Find data entry
    data_entry = (
        db.query(DataEntry)
        .filter(DataEntry.id == item_id, DataEntry.endpoint_id == endpoint.id)
        .first()
    )

    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found in {endpoint_name}",
        )

    # Check ownership - users can only delete their own data unless they're admin
    if not current_user.is_admin and data_entry.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own data",
        )

    # Store data for audit
    old_data = cast(Dict[str, Any], data_entry.data).copy()

    # Soft delete by setting is_active to False
    setattr(data_entry, "is_active", False)
    db.commit()

    # Log audit action
    log_audit_action(
        db,
        "DELETE",
        "data_entries",
        cast(int, data_entry.id),
        current_user,
        old_data,
        None,
        request,
    )
    db.commit()

    return {"message": f"Data deleted from {endpoint_name}"}


# Bulk operations
@router.post("/{endpoint_name}/bulk", response_model=Dict[str, Any])
async def bulk_add_endpoint_data(
    endpoint_name: str,
    data_list: List[Dict[str, Any]],
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Bulk add data to an endpoint (authenticated users only)"""
    # Find endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    success_count = 0
    error_count = 0
    errors = []
    created_items = []

    endpoint_model: Optional[Type[BaseModel]] = get_endpoint_model(endpoint_name)

    for i, data in enumerate(data_list):
        try:
            # Sanitize input
            sanitized_data = sanitize_data_dict(data)

            # Validate data
            if endpoint_model:
                validated_data = endpoint_model(**sanitized_data)
                sanitized_data = validated_data.model_dump(exclude_unset=True)

            # Create data entry
            data_entry = DataEntry(
                endpoint_id=endpoint.id,
                data=sanitized_data,
                created_by_id=current_user.id,
            )
            db.add(data_entry)
            db.flush()  # Get the ID without committing

            created_items.append(data_entry.id)
            success_count += 1

        except Exception as e:
            error_count += 1
            errors.append({"index": i, "data": data, "error": str(e)})

    db.commit()

    return {
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors,
        "created_items": created_items,
        "message": f"Bulk operation completed for {endpoint_name}",
    }


# User-specific public data access (legacy route)
# Use /{endpoint_name}/users/{username} instead
@router.get("/users/{username}/{endpoint_name}", response_model=List[Dict[str, Any]])
async def get_user_public_data_legacy(
    username: str,
    endpoint_name: str,
    level: str = Query(
        "public_full",
        description="Privacy level: business_card, professional, public_full, ai_safe",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(True, description="Filter active items only"),
    db: Session = Depends(get_db),
):
    """
    Legacy user-specific endpoint access (DEPRECATED)
    Use /{endpoint_name}/users/{username} instead for better RESTful design
    """
    # SECURITY: Validate username and endpoint_name for path traversal and injection
    try:
        validate_user_route_security(username, endpoint_name)
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Build redirect URL with query parameters
    query_params = f"?level={level}&page={page}&size={size}&active_only={active_only}"
    redirect_url = f"/api/v1/{endpoint_name}/users/{username}{query_params}"

    # Redirect to the new pattern
    raise HTTPException(
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        detail=f"Use /api/v1/{endpoint_name}/users/{username} instead",
        headers={"Location": redirect_url},
    )


# Privacy settings management
@router.get("/privacy/settings", response_model=Dict[str, Any])
async def get_privacy_settings(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get current user's privacy settings"""
    settings = (
        db.query(UserPrivacySettings)
        .filter(UserPrivacySettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        # Create default settings
        settings = UserPrivacySettings(
            user_id=current_user.id,
            show_contact_info=True,
            show_location=True,
            show_current_company=True,
            show_salary_range=False,
            show_education_details=True,
            show_personal_projects=True,
            business_card_mode=False,
            ai_assistant_access=True,
            custom_privacy_rules={},
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "show_contact_info": settings.show_contact_info,
        "show_location": settings.show_location,
        "show_current_company": settings.show_current_company,
        "show_salary_range": settings.show_salary_range,
        "show_education_details": settings.show_education_details,
        "show_personal_projects": settings.show_personal_projects,
        "business_card_mode": settings.business_card_mode,
        "ai_assistant_access": settings.ai_assistant_access,
        "custom_privacy_rules": settings.custom_privacy_rules,
    }


@router.put("/privacy/settings", response_model=Dict[str, Any])
async def update_privacy_settings(
    settings_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user's privacy settings"""
    settings = (
        db.query(UserPrivacySettings)
        .filter(UserPrivacySettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        settings = UserPrivacySettings(user_id=current_user.id)
        db.add(settings)

    # Update allowed fields
    allowed_fields = {
        "show_contact_info",
        "show_location",
        "show_current_company",
        "show_salary_range",
        "show_education_details",
        "show_personal_projects",
        "business_card_mode",
        "ai_assistant_access",
        "custom_privacy_rules",
    }

    for field, value in settings_data.items():
        if field in allowed_fields:
            setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    return {"message": "Privacy settings updated successfully"}


@router.get("/privacy/preview/{endpoint_name}")
async def preview_privacy_filtering(
    endpoint_name: str,
    level: str = Query("public_full", description="Privacy level to preview"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Preview how your data looks with different privacy levels"""
    from ..privacy import get_privacy_filter

    # Get user's data for the endpoint
    endpoint = (
        db.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_name}' not found",
        )

    # Get user's latest data entry
    data_entry = (
        db.query(DataEntry)
        .filter(
            DataEntry.endpoint_id == endpoint.id,
            DataEntry.created_by_id == current_user.id,
            DataEntry.is_active == True,
        )
        .order_by(DataEntry.created_at.desc())
        .first()
    )

    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for endpoint '{endpoint_name}'",
        )

    # Apply privacy filtering
    privacy_filter = get_privacy_filter(db, current_user)

    # Show both original and filtered versions
    return {
        "original": data_entry.data,
        "filtered": privacy_filter.filter_data(
            cast(Dict[str, Any], data_entry.data),
            privacy_level=level,
            is_authenticated=False,
        ),
        "privacy_level": level,
        "fields_removed": len(str(data_entry.data))
        - len(
            str(
                privacy_filter.filter_data(
                    cast(Dict[str, Any], data_entry.data),
                    privacy_level=level,
                    is_authenticated=False,
                )
            )
        ),
    }


# Data import endpoints
@router.post("/import/user/{username}", response_model=Dict[str, Any])
async def import_user_data(
    username: str,
    data_directory: Optional[str] = Query(
        None, description="Custom data directory path"
    ),
    replace_existing: bool = Query(False, description="Replace existing data"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Import data for a specific user from their data directory (admin only)"""
    from ..multi_user_import import import_user_data_from_directory

    result = import_user_data_from_directory(
        username=username,
        data_directory=data_directory,
        db=db,
        replace_existing=replace_existing,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
        )

    return result


@router.post("/import/all", response_model=Dict[str, Any])
async def import_all_users_data(
    base_directory: str = Query(
        "data/private", description="Base directory containing user folders"
    ),
    replace_existing: bool = Query(False, description="Replace existing data"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Import data for all users from their respective directories (admin only)"""
    from ..multi_user_import import import_all_users_data

    result = import_all_users_data(
        base_directory=base_directory, db=db, replace_existing=replace_existing
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
        )

    return result


@router.post("/import/file", response_model=Dict[str, Any])
async def import_single_file(
    file_path: str = Query(..., description="Path to JSON file to import"),
    endpoint_name: str = Query(..., description="Endpoint name to import to"),
    username: Optional[str] = Query(
        None, description="Username (defaults to current user)"
    ),
    replace_existing: bool = Query(False, description="Replace existing data"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Import a single JSON file to an endpoint"""
    from ..multi_user_import import import_user_file

    # Use provided username or current user's username
    target_username = username if username else cast(str, current_user.username)

    # Only admins can import for other users
    if target_username != current_user.username and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can import data for other users",
        )

    result = import_user_file(
        username=target_username,
        file_path=file_path,
        endpoint_name=endpoint_name,
        db=db,
        replace_existing=replace_existing,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
        )

    return result


@router.post("/setup/user/{username}", response_model=Dict[str, Any])
async def setup_new_user_with_data(
    username: str,
    user_data: UserCreate,
    copy_examples: bool = Query(
        True, description="Copy example files to user directory"
    ),
    import_data: bool = Query(True, description="Import data after setup"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Complete user setup: create user, directory, and import initial data
    (admin only)"""
    from ..database import UserPrivacySettings
    from ..multi_user_import import (
        create_user_data_directory,
        import_user_data_from_directory,
    )

    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{username}' already exists",
        )

    try:
        # 1. Create the user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=user_data.is_admin or False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 2. Create default privacy settings
        privacy_settings = UserPrivacySettings(
            user_id=new_user.id,
            show_contact_info=True,
            show_location=True,
            show_current_company=True,
            show_salary_range=False,
            show_education_details=True,
            show_personal_projects=True,
            business_card_mode=False,
            ai_assistant_access=True,
            custom_privacy_rules={},
        )
        db.add(privacy_settings)
        db.commit()

        # 3. Create user data directory
        user_dir = None
        if copy_examples:
            user_dir = create_user_data_directory(username)

        # 4. Import data if requested
        import_result = None
        if import_data and user_dir:
            import_result = import_user_data_from_directory(
                username=username,
                data_directory=user_dir,
                db=db,
                replace_existing=False,
            )

        return {
            "success": True,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "is_admin": new_user.is_admin,
            },
            "data_directory": user_dir,
            "import_result": import_result,
        }

    except Exception as e:
        # Rollback user creation if something fails
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User setup failed: {str(e)}",
        )
