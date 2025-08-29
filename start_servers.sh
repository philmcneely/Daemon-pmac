#!/bin/bash
"""
Start both API and Frontend servers
API: http://localhost:8007
Frontend: http://localhost:8006
"""

echo "🚀 Starting Daemon Portfolio Services..."
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check ports
if ! check_port 8007; then
    echo "Please stop the service using port 8007 and try again"
    exit 1
fi

if ! check_port 8006; then
    echo "Please stop the service using port 8006 and try again"
    exit 1
fi

echo "✅ Ports 8006 and 8007 are available"
echo ""

# Start API server in background
echo "🔧 Starting API server on port 8007..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007 &
API_PID=$!

# Wait a moment for API to start
sleep 2

# Start frontend server in background
echo "🎨 Starting Frontend server on port 8006..."
python frontend_server.py &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 2

echo ""
echo "🎉 Services are starting up!"
echo "📋 API Documentation: http://localhost:8007/docs"
echo "🌐 Portfolio Frontend: http://localhost:8006/"
echo "📊 API Health Check: http://localhost:8007/health"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "👋 Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
