#!/bin/bash
"""
Multi-App Start Script
Starts servers with app-specific configuration for multi-app hosting
Usage: ./multi-app-start.sh [app-id] [api-port] [frontend-port]
"""

APP_ID=${1:-daemon}
API_PORT=${2:-8007}
FRONTEND_PORT=${3:-8006}

echo "🚀 Starting Multi-App: $APP_ID"
echo "📋 API Port: $API_PORT"
echo "🌐 Frontend Port: $FRONTEND_PORT"
echo ""

# Load app-specific environment if it exists
ENV_FILE=".env.$APP_ID"
if [ -f "$ENV_FILE" ]; then
    echo "📋 Loading app-specific configuration from $ENV_FILE"
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
elif [ -f .env ]; then
    echo "📋 Loading default configuration from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No environment file found, using defaults"
fi

# Override ports from command line
export PORT=$API_PORT
export FRONTEND_PORT=$FRONTEND_PORT
export DEPLOYMENT_MODE=multi-app

# Set app-specific paths for reverse proxy
export API_BASE_PATH="/$APP_ID/api"
export FRONTEND_BASE_PATH="/$APP_ID"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $1 is already in use"
        return 1
    fi
    return 0
}

echo "🔍 Checking ports for app: $APP_ID"
if ! check_port $API_PORT; then
    echo "Please stop the service using port $API_PORT and try again"
    exit 1
fi

if ! check_port $FRONTEND_PORT; then
    echo "Please stop the service using port $FRONTEND_PORT and try again"
    exit 1
fi

echo "✅ Ports $API_PORT and $FRONTEND_PORT are available"
echo ""

# Create PID file directory
mkdir -p /tmp/daemon-apps

# Start API server
echo "🔧 Starting API server for $APP_ID on port $API_PORT..."
python -m uvicorn app.main:app --host 0.0.0.0 --port $API_PORT &
API_PID=$!
echo $API_PID > "/tmp/daemon-apps/$APP_ID-api.pid"

# Wait for API to start
sleep 3

# Start frontend server
echo "🎨 Starting Frontend server for $APP_ID on port $FRONTEND_PORT..."
python frontend_server.py &
FRONTEND_PID=$!
echo $FRONTEND_PID > "/tmp/daemon-apps/$APP_ID-frontend.pid"

echo ""
echo "🎉 Multi-app servers for '$APP_ID' are running!"
echo "📋 API: http://localhost:$API_PORT (proxy to /$APP_ID/api/)"
echo "🌐 Frontend: http://localhost:$FRONTEND_PORT (proxy to /$APP_ID/)"
echo ""
echo "💡 Example nginx config:"
echo "   location /$APP_ID/api/ {"
echo "       proxy_pass http://localhost:$API_PORT/;"
echo "   }"
echo "   location /$APP_ID/ {"
echo "       proxy_pass http://localhost:$FRONTEND_PORT/;"
echo "   }"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping $APP_ID servers..."
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f "/tmp/daemon-apps/$APP_ID-api.pid"
    rm -f "/tmp/daemon-apps/$APP_ID-frontend.pid"
    echo "👋 $APP_ID servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
