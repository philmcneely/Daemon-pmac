"""
Main FastAPI application
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .auth import add_security_headers, check_ip_access
from .config import settings
from .database import SessionLocal, create_default_endpoints, init_db

# Import routers
from .routers import admin, api, auth, mcp
from .schemas import HealthResponse
from .utils import cleanup_old_backups, create_backup, get_uptime, health_check

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.logging_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Startup time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Daemon application...")

    # Initialize database
    try:
        init_db()
        db = SessionLocal()
        create_default_endpoints(db)
        db.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # Create backup directory
    if settings.backup_enabled:
        os.makedirs(settings.backup_dir, exist_ok=True)

    # Schedule background tasks
    if settings.backup_enabled:
        # Create initial backup
        try:
            backup_info = create_backup()
            logger.info(f"Initial backup created: {backup_info.filename}")
        except Exception as e:
            logger.warning(f"Initial backup failed: {e}")

        # Schedule daily backups (simplified - in production use proper
        # scheduler)
        asyncio.create_task(daily_backup_task())

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Daemon application...")


async def daily_backup_task():
    """Background task for daily backups"""
    while True:
        try:
            # Wait 24 hours
            await asyncio.sleep(86400)

            # Create backup
            if settings.backup_enabled:
                backup_info = create_backup()
                logger.info(
                    f"Scheduled backup created: {
                        backup_info.filename}"
                )

                # Cleanup old backups
                cleanup_old_backups()
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")


# Create FastAPI app
app = FastAPI(
    title="Daemon API",
    version=settings.version,
    description="""
## 🚀 Daemon Personal API Framework

A **production-ready personal API framework** that seamlessly scales from single-user simplicity to multi-user complexity with comprehensive privacy controls.

### ✨ Key Features

- **🔄 Adaptive Multi-User Support**: Automatically switches between single-user and multi-user modes
- **🔐 Advanced Privacy System**: Configurable privacy levels (business_card, professional, public_full, ai_safe)
- **🎯 Dynamic Endpoints**: Create custom endpoints via API or CLI
- **📊 Comprehensive Data Management**: Full CRUD operations with validation
- **🛡️ Security First**: JWT authentication, rate limiting, input validation
- **🏥 Production Ready**: Health monitoring, metrics, automatic backups

### 🔄 Adaptive Routing System

The API automatically adapts based on the number of users:

**Single User Mode (≤1 user):**
- `GET /api/v1/resume` - Simple, clean endpoints
- `GET /api/v1/ideas`
- `GET /api/v1/skills`

**Multi-User Mode (2+ users):**
- `GET /api/v1/resume/users/{username}` - User-specific endpoints
- `GET /api/v1/ideas/users/{username}`
- `GET /api/v1/skills/users/{username}`

### 🔐 Privacy Levels

All endpoints support privacy filtering:
- `business_card` - Minimal information for networking
- `professional` - Work-appropriate details
- `public_full` - Full public information
- `ai_safe` - AI-assistant safe data (no sensitive info)

### 📚 Available Endpoints

Core personal data endpoints:
- **resume** - Professional resume and work history
- **skills** - Technical and soft skills
- **ideas** - Ideas and thoughts
- **favorite_books** - Book recommendations
- **hobbies** - Hobbies and interests
- **problems** - Problems seeking solutions
- **looking_for** - What you're actively seeking
- **about** - Personal/entity information

### 🔗 Useful Links

- **Authentication**: Use `/auth/login` to get JWT tokens
- **System Info**: Check `/api/v1/system/info` for current mode
- **Health Check**: Monitor system status at `/health`
- **Create Endpoints**: Admin users can create custom endpoints

### 💡 Getting Started

1. **Login**: Use `/auth/login` to get your JWT token
2. **Explore**: Browse available endpoints at `/api/v1/endpoints`
3. **Create Data**: Add your information to various endpoints
4. **Customize**: Create custom endpoints for your specific needs

*Inspired by [Daniel Miessler's Daemon project](https://github.com/danielmiessler/Daemon)*
    """,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
    contact={
        "name": "Daemon API Support",
        "url": "https://github.com/yourusername/Daemon",
        "email": "support@example.com",
    },
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    tags_metadata=[
        {
            "name": "Root",
            "description": "🏠 **Basic Information** - Root endpoint and basic app info",
        },
        {
            "name": "Authentication",
            "description": "🔐 **Authentication & Authorization** - Login, registration, and user management",
        },
        {
            "name": "Daemon API",
            "description": "📊 **Core Data Endpoints** - Dynamic personal data endpoints with privacy filtering",
        },
        {
            "name": "Administration",
            "description": "👑 **Admin Management** - User administration, system management (Admin only)",
        },
        {
            "name": "Monitoring",
            "description": "🏥 **System Health** - Health checks, metrics, and system status monitoring",
        },
        {
            "name": "MCP",
            "description": "🤖 **Model Context Protocol** - AI integration endpoints for LLM access",
        },
    ],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security middleware for IP filtering and headers"""

    # IP access control
    if settings.allowed_ips:
        try:
            check_ip_access(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

    # Process request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Add security headers
    response = add_security_headers(response)

    # Add performance header
    response.headers["X-Process-Time"] = str(process_time)

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )

    return response


# Include routers
app.include_router(auth.router)
app.include_router(api.router)
app.include_router(admin.router)
if settings.mcp_enabled:
    app.include_router(mcp.router)


def get_available_endpoints():
    """Get list of available endpoint names from database"""
    try:
        from .database import Endpoint, SessionLocal

        db = SessionLocal()
        try:
            endpoints = db.query(Endpoint).filter(Endpoint.is_active).all()
            return [ep.name for ep in endpoints]
        finally:
            db.close()
    except Exception:
        # Fallback to core endpoints if database query fails
        return [
            "resume",
            "skills",
            "ideas",
            "favorite_books",
            "hobbies",
            "problems",
            "looking_for",
            "about",
        ]


def custom_openapi():
    """Generate enhanced OpenAPI schema with dynamic endpoint examples and enums"""
    if app.openapi_schema:
        return app.openapi_schema

    # Get default OpenAPI schema using FastAPI's get_openapi function
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Get available endpoints dynamically
    available_endpoints = get_available_endpoints()

    # Enhance the schema with dynamic endpoint examples
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }

    # Add dynamic path examples to the schema
    paths = openapi_schema.get("paths", {})

    # Update existing paths to add enum constraints to endpoint_name parameters
    paths_to_update = []
    for path, path_item in paths.items():
        if "/{endpoint_name}" in path:
            paths_to_update.append((path, path_item))

    for path, path_item in paths_to_update:
        for method, operation in path_item.items():
            if isinstance(operation, dict) and "parameters" in operation:
                for param in operation["parameters"]:
                    if (
                        param.get("name") == "endpoint_name"
                        and param.get("in") == "path"
                    ):
                        # Add enum constraint with available endpoints
                        param["schema"]["enum"] = available_endpoints
                        param["description"] = (
                            f"Endpoint name (available: {
                                ', '.join(available_endpoints)})"
                        )

    # Add example endpoints in the description
    core_endpoints = available_endpoints

    # Enhance the generic {endpoint_name} paths with concrete examples
    for endpoint in core_endpoints:
        # Add GET endpoint examples
        example_get_path = f"/api/v1/{endpoint}"
        if example_get_path not in paths:
            paths[example_get_path] = {
                "get": {
                    "tags": ["Daemon API"],
                    "summary": f"Get {endpoint} data",
                    "description": f"Get data from the {endpoint} endpoint. This is a concrete example of the dynamic /api/v1/{{endpoint_name}} pattern.",
                    "operationId": f"get_{endpoint}_data",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "minimum": 1, "default": 1},
                            "description": "Page number for pagination",
                        },
                        {
                            "name": "size",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 50,
                            },
                            "description": "Items per page",
                        },
                        {
                            "name": "privacy_level",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "enum": [
                                    "business_card",
                                    "professional",
                                    "public_full",
                                    "ai_safe",
                                ],
                            },
                            "description": "Privacy filtering level",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": f"List of {endpoint} data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"},
                                    }
                                }
                            },
                        }
                    },
                }
            }

        # Add user-specific GET endpoint examples for multi-user mode
        user_example_path = f"/api/v1/{endpoint}/users/{{username}}"
        if user_example_path not in paths:
            paths[user_example_path] = {
                "get": {
                    "tags": ["Daemon API"],
                    "summary": f"Get {endpoint} data for specific user",
                    "description": f"Get {endpoint} data for a specific user (multi-user mode). Use this pattern when multiple users exist in the system.",
                    "operationId": f"get_{endpoint}_user_data",
                    "parameters": [
                        {
                            "name": "username",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Username to get data for",
                        },
                        {
                            "name": "level",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "enum": [
                                    "business_card",
                                    "professional",
                                    "public_full",
                                    "ai_safe",
                                ],
                                "default": "public_full",
                            },
                            "description": "Privacy filtering level",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": f"List of {endpoint} data for the user",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"},
                                    }
                                }
                            },
                        }
                    },
                }
            }

    openapi_schema["paths"] = paths
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Set the custom OpenAPI generator
app.openapi = custom_openapi


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic information"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": settings.description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "docs_url": settings.docs_url,
        "health_url": "/health",
        "api_prefix": settings.api_prefix,
        "mcp_enabled": settings.mcp_enabled,
    }


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health():
    """Health check endpoint"""
    health_data = health_check()

    # Add application-specific info
    health_data.update(
        {
            "version": settings.version,
            "uptime_seconds": get_uptime(),
            "database": health_data["checks"]["database"]["status"] == "healthy",
        }
    )

    # Remove detailed checks from response (keep simple for load balancers)
    status_code = 200 if health_data["status"] == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": health_data["status"],
            "timestamp": health_data["timestamp"],
            "version": settings.version,
            "database": health_data["database"],
            "uptime_seconds": health_data["uptime_seconds"],
        },
    )


# Metrics endpoint (Prometheus format)
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus-style metrics endpoint"""
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")

    from .database import DataEntry, Endpoint, SessionLocal, User
    from .utils import get_system_metrics

    try:
        # Get system metrics
        system_metrics = get_system_metrics()

        # Get database metrics
        db = SessionLocal()

        total_entries = db.query(DataEntry).count()
        active_entries = db.query(DataEntry).filter(DataEntry.is_active).count()
        total_endpoints = db.query(Endpoint).count()
        active_endpoints = db.query(Endpoint).filter(Endpoint.is_active).count()
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active).count()

        db.close()

        # Format as Prometheus metrics
        metrics_output = f"""# HELP daemon_info Application information
# TYPE daemon_info gauge
daemon_info{{version="{settings.version}"}} 1

# HELP daemon_uptime_seconds Application uptime in seconds
# TYPE daemon_uptime_seconds counter
daemon_uptime_seconds {get_uptime()}

# HELP daemon_data_entries_total Total number of data entries
# TYPE daemon_data_entries_total gauge
daemon_data_entries_total{{status="active"}} {active_entries}
daemon_data_entries_total{{status="total"}} {total_entries}

# HELP daemon_endpoints_total Total number of endpoints
# TYPE daemon_endpoints_total gauge
daemon_endpoints_total{{status="active"}} {active_endpoints}
daemon_endpoints_total{{status="total"}} {total_endpoints}

# HELP daemon_users_total Total number of users
# TYPE daemon_users_total gauge
daemon_users_total{{status="active"}} {active_users}
daemon_users_total{{status="total"}} {total_users}

# HELP daemon_memory_usage_percent Memory usage percentage
# TYPE daemon_memory_usage_percent gauge
daemon_memory_usage_percent {system_metrics['memory']['percent']}

# HELP daemon_cpu_usage_percent CPU usage percentage
# TYPE daemon_cpu_usage_percent gauge
daemon_cpu_usage_percent {system_metrics['cpu']['percent']}

# HELP daemon_disk_usage_percent Disk usage percentage
# TYPE daemon_disk_usage_percent gauge
daemon_disk_usage_percent {system_metrics['disk']['percent']}

# HELP daemon_database_size_bytes Database size in bytes
# TYPE daemon_database_size_bytes gauge
daemon_database_size_bytes {system_metrics['database']['size_bytes']}
"""

        return Response(content=metrics_output, media_type="text/plain")

    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail="Error generating metrics")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"The requested resource was not found: {
                request.url.path}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Rate limited endpoints
@app.get("/api/v1/rate-limited-example")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def rate_limited_example(request: Request):
    """Example of a rate-limited endpoint"""
    return {"message": "This endpoint is rate limited"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.host, port=settings.port, reload=settings.reload
    )
