#!/bin/bash
"""
Production Start Script
Starts servers for production deployment with environment configuration
"""

echo "🚀 Starting Daemon Portfolio - Production Mode"
echo ""

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading configuration from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ No .env file found. Please create one based on .env.example"
    exit 1
fi

# Set production defaults
export DEPLOYMENT_MODE=production
export PORT=${PORT:-8004}
export FRONTEND_PORT=${FRONTEND_PORT:-8005}

# Validate required environment variables
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-super-secret-key-here-change-me" ]; then
    echo "❌ Please set a secure SECRET_KEY in your .env file"
    exit 1
fi

echo "🔍 Starting production servers..."
echo "📋 API Server: http://localhost:$PORT"
echo "🌐 Frontend Server: http://localhost:$FRONTEND_PORT"

# Check if we should run single server mode (legacy)
if [ "$PORT" = "8004" ]; then
    echo "🔄 Single server mode detected (port 8004)"
    echo "🔧 Starting combined API + Frontend server..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
else
    echo "🔄 Dual server mode detected"

    # Start API server
    echo "🔧 Starting API server..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT &
    API_PID=$!

    # Wait for API to start
    sleep 3

    # Start frontend server
    echo "🎨 Starting Frontend server..."
    python frontend_server.py &
    FRONTEND_PID=$!

    # Function to cleanup on exit
    cleanup() {
        echo ""
        echo "🛑 Stopping production servers..."
        kill $API_PID 2>/dev/null
        kill $FRONTEND_PID 2>/dev/null
        echo "👋 Production servers stopped"
        exit 0
    }

    # Set trap to cleanup on script exit
    trap cleanup SIGINT SIGTERM

    echo ""
    echo "🎉 Production servers are running!"
    echo "Press Ctrl+C to stop both services"

    # Wait for background processes
    wait
fi
