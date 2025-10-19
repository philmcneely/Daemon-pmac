"""
Module: main
Description: Main FastAPI application with middleware, routing, and lifecycle
             management for the Daemon personal API framework.

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, List, cast

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.auth import add_security_headers, check_ip_access
from app.config import settings
from app.database import SessionLocal, create_default_endpoints, init_db
from app.routers import admin, api, auth, mcp
from app.schemas import HealthResponse
from app.utils import cleanup_old_backups, create_backup, get_uptime, health_check


# ----------------------------------------------------------------------
# Application factory
# ----------------------------------------------------------------------
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Daemon API",
        version=settings.version,
        description="Daemon Personal API Framework – a production‑ready personal API.",
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
        contact={
            "name": "Daemon API Support",
            "url": "https://github.com/yourusername/Daemon",
            "email": "support@example.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        tags_metadata=[
            {"name": "Root", "description": "🏠 Basic information"},
            {"name": "Authentication", "description": "🔐 Login & user management"},
            {"name": "Daemon API", "description": "📊 Core data endpoints"},
            {"name": "Administration", "description": "👑 Admin management"},
            {"name": "Monitoring", "description": "🏥 System health"},
            {"name": "MCP", "description": "🤖 Model Context Protocol"},
        ],
    )
    return app


# ----------------------------------------------------------------------
# Lifespan events
# ----------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown."""
    logger.info("Starting Daemon application...")

    # Initialise DB and default endpoints
    try:
        init_db()
        db = SessionLocal()
        create_default_endpoints(db)
        db.close()
        logger.info("Database initialised")
    except Exception as e:
        logger.error(f"Database initialisation failed: {e}")
        raise

    # Ensure backup directory exists
    if settings.backup_enabled:
        os.makedirs(settings.backup_dir, exist_ok=True)

    # Schedule daily backup task if enabled
    if settings.backup_enabled:
        try:
            backup_info = create_backup()
            logger.info(f"Initial backup created: {backup_info.filename}")
        except Exception as e:
            logger.warning(f"Initial backup failed: {e}")

        asyncio.create_task(daily_backup_task())

    logger.info("Application startup complete")
    yield
    logger.info("Shutting down Daemon application...")


# ----------------------------------------------------------------------
# Background backup task
# ----------------------------------------------------------------------
async def daily_backup_task():
    """Create daily backups and clean old ones."""
    while True:
        try:
            await asyncio.sleep(86400)  # 24 h
            if settings.backup_enabled:
                info = create_backup()
                logger.info(f"Scheduled backup created: {info.filename}")
                cleanup_old_backups()
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")


# ----------------------------------------------------------------------
# Initialise app, logging and middleware
# ----------------------------------------------------------------------
app = create_app()

# Setup logging
log_handler = logging.StreamHandler()
log_formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.logging_level.upper()))
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(log_handler)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# Security middleware (IP filtering & headers)
# ----------------------------------------------------------------------
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path.startswith("/mcp"):
        # MCP endpoints are public
        pass
    elif settings.allowed_ips:
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

    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    response = add_security_headers(response)
    response.headers["X-Process-Time"] = str(duration)

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    return response


# ----------------------------------------------------------------------
# Router inclusion
# ----------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(api.router)
app.include_router(admin.router)
if settings.mcp_enabled:
    app.include_router(mcp.router)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_available_endpoints() -> List[str]:
    """Return list of active endpoint names."""
    try:
        from app.database import Endpoint, SessionLocal

        db = SessionLocal()
        try:
            eps = db.query(Endpoint).filter(Endpoint.is_active).all()
            return [e.name for e in eps]
        finally:
            db.close()
    except Exception:
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
    """Generate OpenAPI schema with dynamic examples."""
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    endpoints = cast(List[str], get_available_endpoints())
    schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }

    # Add enum constraints to endpoint_name parameters
    for path, path_item in schema.get("paths", {}).items():
        if "/{endpoint_name}" in path:
            for operation in path_item.values():
                if isinstance(operation, dict) and "parameters" in operation:
                    for param in operation["parameters"]:
                        if (
                            param.get("name") == "endpoint_name"
                            and param.get("in") == "path"
                        ):
                            param["schema"]["enum"] = endpoints
                            param["description"] = (
                                f"Endpoint name (available: {', '.join(endpoints)})"
                            )

    # Add concrete example paths
    for ep in endpoints:
        get_path = f"/api/v1/{ep}"
        if get_path not in schema["paths"]:
            schema["paths"][get_path] = {
                "get": {
                    "tags": ["Daemon API"],
                    "summary": f"Get {ep} data",
                    "operationId": f"get_{ep}_data",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "minimum": 1, "default": 1},
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
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": f"List of {ep} data",
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

        user_path = f"/api/v1/{ep}/users/{{username}}"
        if user_path not in schema["paths"]:
            schema["paths"][user_path] = {
                "get": {
                    "tags": ["Daemon API"],
                    "summary": f"Get {ep} data for specific user",
                    "operationId": f"get_{ep}_user_data",
                    "parameters": [
                        {
                            "name": "username",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
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
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": f"List of {ep} data for the user",
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

    app.openapi_schema = schema
    return app.openapi_schema


setattr(app, "openapi", custom_openapi)


# ----------------------------------------------------------------------
# Core endpoints
# ----------------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root():
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


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health():
    data = health_check()
    data.update(
        {
            "version": settings.version,
            "uptime_seconds": get_uptime(),
            "database": data["checks"]["database"]["status"] == "healthy",
        }
    )
    status_code = 200 if data["status"] == "healthy" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": data["status"],
            "timestamp": data["timestamp"],
            "version": settings.version,
            "database": data["database"],
            "uptime_seconds": data["uptime_seconds"],
        },
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    from app.database import DataEntry, Endpoint, SessionLocal, User
    from app.utils import get_system_metrics

    try:
        sys_metrics = get_system_metrics()
        db = SessionLocal()
        total_entries = db.query(DataEntry).count()
        active_entries = db.query(DataEntry).filter(DataEntry.is_active).count()
        total_endpoints = db.query(Endpoint).count()
        active_endpoints = db.query(Endpoint).filter(Endpoint.is_active).count()
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active).count()
        db.close()
        output = (
            f"# HELP daemon_info Application information\n"
            f"# TYPE daemon_info gauge\n"
            f'daemon_info{{version="{settings.version}"}} 1\n\n'
            f"# HELP daemon_uptime_seconds Application uptime in seconds\n"
            f"# TYPE daemon_uptime_seconds counter\n"
            f"daemon_uptime_seconds {get_uptime()}\n\n"
            f"# HELP daemon_data_entries_total Total number of data entries\n"
            f"# TYPE daemon_data_entries_total gauge\n"
            f'daemon_data_entries_total{{status="active"}} {active_entries}\n'
            f'daemon_data_entries_total{{status="total"}} {total_entries}\n\n'
            f"# HELP daemon_endpoints_total Total number of endpoints\n"
            f"# TYPE daemon_endpoints_total gauge\n"
            f'daemon_endpoints_total{{status="active"}} {active_endpoints}\n'
            f'daemon_endpoints_total{{status="total"}} {total_endpoints}\n\n'
            f"# HELP daemon_users_total Total number of users\n"
            f"# TYPE daemon_users_total gauge\n"
            f'daemon_users_total{{status="active"}} {active_users}\n'
            f'daemon_users_total{{status="total"}} {total_users}\n\n'
            f"# HELP daemon_memory_usage_percent Memory usage percentage\n"
            f"# TYPE daemon_memory_usage_percent gauge\n"
            f"daemon_memory_usage_percent {sys_metrics['memory']['percent']}\n\n"
            f"# HELP daemon_cpu_usage_percent CPU usage percentage\n"
            f"# TYPE daemon_cpu_usage_percent gauge\n"
            f"daemon_cpu_usage_percent {sys_metrics['cpu']['percent']}\n\n"
            f"# HELP daemon_disk_usage_percent Disk usage percentage\n"
            f"# TYPE daemon_disk_usage_percent gauge\n"
            f"daemon_disk_usage_percent {sys_metrics['disk']['percent']}\n\n"
            f"# HELP daemon_database_size_bytes Database size in bytes\n"
            f"# TYPE daemon_database_size_bytes gauge\n"
            f"daemon_database_size_bytes {sys_metrics['database']['size_bytes']}"
        )
        return Response(content=output, media_type="text/plain")
    except Exception as e:
        logger.error(f"Metrics generation error: {e}")
        raise HTTPException(status_code=500, detail="Error generating metrics")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"The requested resource was not found: {request.url.path}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/api/v1/rate-limited-example")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def rate_limited_example(request: Request):
    return {"message": "This endpoint is rate limited"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.host, port=settings.port, reload=settings.reload
    )
