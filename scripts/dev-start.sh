#!/bin/bash
"""
Development Start Script
Starts both API and Frontend servers for local development
"""

echo "🚀 Starting Daemon Portfolio - Development Mode"
echo ""

# Load environment if .env exists
if [ -f .env ]; then
    echo "📋 Loading configuration from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "📋 Using default configuration (no .env file found)"
fi

# Set development defaults
export DEPLOYMENT_MODE=development
export PORT=${PORT:-8004}
export FRONTEND_PORT=${FRONTEND_PORT:-8005}

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $1 is already in use"
        return 1
    fi
    return 0
}

echo "🔍 Checking ports..."
if ! check_port $PORT; then
    echo "Please stop the service using port $PORT and try again"
    exit 1
fi

if ! check_port $FRONTEND_PORT; then
    echo "Please stop the service using port $FRONTEND_PORT and try again"
    exit 1
fi

echo "✅ Ports $PORT and $FRONTEND_PORT are available"
echo ""

# Start API server in background
echo "🔧 Starting API server on port $PORT..."
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload &
API_PID=$!

# Wait for API to start
sleep 3

# Start frontend server in background
echo "🎨 Starting Frontend server on port $FRONTEND_PORT..."
python frontend_server.py &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 2

echo ""
echo "🎉 Development servers are running!"
echo "📋 API Documentation: http://localhost:$PORT/docs"
echo "🌐 Portfolio Frontend: http://localhost:$FRONTEND_PORT/"
echo "📊 API Health Check: http://localhost:$PORT/health"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping development servers..."
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "👋 Development servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
