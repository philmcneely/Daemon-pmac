#!/usr/bin/env python3
"""
Simple HTTP server for serving the portfolio frontend.
Supports environment-based configuration for multi-app hosting.
"""

import http.server
import os
import socketserver
import sys
from pathlib import Path


def get_config():
    """Load configuration from environment variables."""
    # Simple environment variable loading
    frontend_port = 8006
    api_port = 8007

    if os.getenv("FRONTEND_PORT"):
        frontend_port = int(os.getenv("FRONTEND_PORT"))
    elif os.getenv("DAEMON_FRONTEND_PORT"):
        frontend_port = int(os.getenv("DAEMON_FRONTEND_PORT"))

    if os.getenv("PORT"):
        api_port = int(os.getenv("PORT"))
    elif os.getenv("DAEMON_API_PORT"):
        api_port = int(os.getenv("DAEMON_API_PORT"))

    return {
        "host": os.getenv("DAEMON_FRONTEND_HOST", "0.0.0.0"),
        "port": frontend_port,
        "api_port": api_port,
        "api_url": os.getenv("DAEMON_API_URL"),
        "base_path": os.getenv("FRONTEND_BASE_PATH", ""),
        "external_domain": os.getenv("EXTERNAL_DOMAIN"),
        "deployment_mode": os.getenv("DEPLOYMENT_MODE", "development"),
    }


# Get configuration
config = get_config()
HOST = config["host"]
PORT = config["port"]

# Get the frontend directory path
frontend_dir = Path(__file__).parent / "frontend"

if not frontend_dir.exists():
    print(f"Error: Frontend directory not found at {frontend_dir}")
    sys.exit(1)

# Change to frontend directory
os.chdir(frontend_dir)


class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve index.html for all paths (SPA support)"""

    def end_headers(self):
        # Add CORS headers for API access
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_GET(self):
        # If requesting root or a path that doesn't exist, serve index.html
        if self.path == "/" or self.path == "/index.html":
            self.path = "/index.html"
        elif (
            not os.path.exists(f".{self.path}")
            and not self.path.startswith("/css/")
            and not self.path.startswith("/js/")
        ):
            self.path = "/index.html"

        return super().do_GET()


if __name__ == "__main__":
    try:
        with socketserver.TCPServer((HOST, PORT), HTTPRequestHandler) as httpd:
            print(f"🚀 Frontend server running at http://localhost:{PORT}/")
            print(f"📁 Serving files from: {frontend_dir}")
            print(f"🔗 API server should be running at http://localhost:8007/")
            print("Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(
                f"❌ Port {PORT} is already in use. "
                "Please stop any existing server on this port."
            )
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
