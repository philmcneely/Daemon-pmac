"""
Module: app
Description: Daemon-pmac Personal API Framework main application package

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- fastapi: 0.104.1+ - Core web framework
- sqlalchemy: 2.0+ - Database ORM

Usage:
    from app.main import app

    # Main FastAPI application instance available for deployment

Notes:
    - Entry point for the Daemon personal API framework
    - Contains all core modules and routers
    - Configured for production deployment
"""

from .main import app  # noqa: F401

__version__ = "0.1.0"
__author__ = "Phil McNeely"
__description__ = "A lightweight, secure personal API framework"
