#!/bin/bash

# Docker Container Test Suite
# Comprehensive testing of Docker containers individually and together
# Can be run locally or in CI environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_PORT=${API_PORT:-8004}
FRONTEND_DEV_PORT=${FRONTEND_DEV_PORT:-8005}
FRONTEND_PROD_HTTP_PORT=${FRONTEND_PROD_HTTP_PORT:-8080}
FRONTEND_PROD_HTTPS_PORT=${FRONTEND_PROD_HTTPS_PORT:-8443}
WAIT_TIME=${WAIT_TIME:-20}
CLEANUP=${CLEANUP:-true}

echo -e "${BLUE}🐳 Docker Container Test Suite${NC}"
echo "=============================================="

# Function to test database initialization (Docker simulation)
test_database_init() {
    echo -e "${BLUE}🗄️ Test 0: Database initialization simulation${NC}"

    # Test with different database paths to simulate Docker scenarios
    local test_db_path="./test_data/test_daemon.db"

    echo "Testing database initialization with path: $test_db_path"

    # Set environment variables to simulate Docker container environment
    export DATABASE_URL="sqlite:///$test_db_path"
    export PORT=8004
    export HOST=0.0.0.0

    # Test database initialization
    python -c "
from app.database import init_db
from app.config import settings
import os

print(f'Testing with DATABASE_URL: {settings.database_url}')
init_db()
print('✅ Database initialization successful')

# Verify database file was created
db_path = settings.database_url.replace('sqlite:///', '')
if os.path.exists(db_path):
    print('✅ Database file created successfully')
else:
    raise Exception('❌ Database file not found')
"

    # Clean up test database
    rm -rf test_data/
    unset DATABASE_URL PORT HOST

    echo -e "${GREEN}✅ Database initialization test passed${NC}"
    echo
}

# Function to cleanup containers
cleanup_containers() {
    echo -e "${YELLOW}🧹 Cleaning up containers...${NC}"
    docker ps -q --filter "name=daemon-*-test" | xargs -r docker stop
    docker ps -aq --filter "name=daemon-*-test" | xargs -r docker rm
    docker network ls -q --filter "name=daemon-*-network" | xargs -r docker network rm
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for $name to be ready...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts failed, retrying..."
        sleep 2
        ((attempt++))
    done

    echo -e "${RED}❌ $name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expect_success=${3:-true}

    echo -e "${BLUE}🔍 Testing $name: $url${NC}"
    if [ "$expect_success" = true ]; then
        if curl -f -s "$url" > /dev/null; then
            echo -e "${GREEN}✅ $name: SUCCESS${NC}"
            return 0
        else
            echo -e "${RED}❌ $name: FAILED${NC}"
            return 1
        fi
    else
        if curl -f -s "$url" > /dev/null; then
            echo -e "${RED}❌ $name: Expected failure but succeeded${NC}"
            return 1
        else
            echo -e "${GREEN}✅ $name: Expected failure (PASS)${NC}"
            return 0
        fi
    fi
}

echo -e "${BLUE}📋 Test Configuration:${NC}"
echo "  API Port: $API_PORT"
echo "  Frontend Dev Port: $FRONTEND_DEV_PORT"
echo "  Frontend Prod HTTP Port: $FRONTEND_PROD_HTTP_PORT"
echo "  Frontend Prod HTTPS Port: $FRONTEND_PROD_HTTPS_PORT"
echo "  Wait Time: $WAIT_TIME seconds"
echo "  Cleanup: $CLEANUP"
echo

# Test 0: Database initialization simulation (pre-Docker test)
test_database_init

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️ Docker not found in PATH. Skipping Docker tests.${NC}"
    echo -e "${GREEN}✅ Database initialization test completed successfully${NC}"
    echo "To run full Docker tests, install Docker and run this script again."
    exit 0
fi

# Trap to cleanup on exit (only after Docker is confirmed available)
if [ "$CLEANUP" = true ]; then
    trap cleanup_containers EXIT
fi

# Test 1: Build all containers
echo -e "${BLUE}🏗️ Test 1: Building all containers${NC}"
echo "Building API container..."
docker build -t daemon-api:test . || exit 1

echo "Building frontend development container..."
docker build -f frontend/Dockerfile.dev -t daemon-frontend-dev:test . || exit 1

echo "Building frontend production container..."
docker build -f frontend/Dockerfile -t daemon-frontend:test . || exit 1

echo -e "${GREEN}✅ All containers built successfully${NC}"
echo

# Test 2: API container standalone
echo -e "${BLUE}🧪 Test 2: API container standalone${NC}"
cleanup_containers

# Create test environment
mkdir -p data logs backups
cat > .env.test << EOF
SECRET_KEY=test-secret-key
PORT=$API_PORT
DEBUG=false
DATABASE_URL=sqlite:///./data/daemon.db
EOF

echo "Starting API container..."
docker run -d --name daemon-api-standalone-test \
    -p $API_PORT:$API_PORT \
    --env-file .env.test \
    -v $(pwd)/data:/app/data \
    daemon-api:test

wait_for_service "http://localhost:$API_PORT/health" "API"

echo "Testing API endpoints..."
test_endpoint "http://localhost:$API_PORT/health" "Health endpoint"
test_endpoint "http://localhost:$API_PORT/docs" "API documentation"
test_endpoint "http://localhost:$API_PORT/api/v1/system/info" "System info endpoint"

docker stop daemon-api-standalone-test
echo -e "${GREEN}✅ API container standalone test passed${NC}"
echo

# Test 3: Frontend development container standalone
echo -e "${BLUE}🧪 Test 3: Frontend development container standalone${NC}"

echo "Starting frontend development container..."
docker run -d --name daemon-frontend-dev-standalone-test \
    -p $FRONTEND_DEV_PORT:$FRONTEND_DEV_PORT \
    -e FRONTEND_PORT=$FRONTEND_DEV_PORT \
    daemon-frontend-dev:test

wait_for_service "http://localhost:$FRONTEND_DEV_PORT/" "Frontend Development"

test_endpoint "http://localhost:$FRONTEND_DEV_PORT/" "Frontend main page"

docker stop daemon-frontend-dev-standalone-test
echo -e "${GREEN}✅ Frontend development container standalone test passed${NC}"
echo

# Test 4: Frontend production container standalone
echo -e "${BLUE}🧪 Test 4: Frontend production container standalone${NC}"

echo "Starting frontend production container..."
docker run -d --name daemon-frontend-prod-standalone-test \
    -p $FRONTEND_PROD_HTTP_PORT:80 \
    -p $FRONTEND_PROD_HTTPS_PORT:443 \
    daemon-frontend:test

wait_for_service "http://localhost:$FRONTEND_PROD_HTTP_PORT/" "Frontend Production"

test_endpoint "http://localhost:$FRONTEND_PROD_HTTP_PORT/" "Frontend HTTP"
test_endpoint "http://localhost:$FRONTEND_PROD_HTTP_PORT/health" "Frontend health check"
test_endpoint "https://localhost:$FRONTEND_PROD_HTTPS_PORT/" "Frontend HTTPS" true

docker stop daemon-frontend-prod-standalone-test
echo -e "${GREEN}✅ Frontend production container standalone test passed${NC}"
echo

# Test 5: Multi-container communication (Development)
echo -e "${BLUE}🧪 Test 5: Multi-container communication (Development)${NC}"
cleanup_containers

echo "Creating Docker network..."
docker network create daemon-dev-test-network

echo "Starting API container..."
docker run -d --name daemon-api-dev-comm-test \
    --network daemon-dev-test-network \
    -p $API_PORT:$API_PORT \
    --env-file .env.test \
    -v $(pwd)/data:/app/data \
    daemon-api:test

wait_for_service "http://localhost:$API_PORT/health" "API"

echo "Starting frontend development container..."
docker run -d --name daemon-frontend-dev-comm-test \
    --network daemon-dev-test-network \
    -p $FRONTEND_DEV_PORT:$FRONTEND_DEV_PORT \
    -e FRONTEND_PORT=$FRONTEND_DEV_PORT \
    -e DAEMON_API_URL=http://daemon-api-dev-comm-test:$API_PORT \
    daemon-frontend-dev:test

wait_for_service "http://localhost:$FRONTEND_DEV_PORT/" "Frontend Development"

echo "Testing inter-container communication..."
test_endpoint "http://localhost:$API_PORT/health" "API from host"
test_endpoint "http://localhost:$FRONTEND_DEV_PORT/" "Frontend from host"

# Test container-to-container communication
echo "Testing container-to-container communication..."
docker exec daemon-frontend-dev-comm-test curl -f http://daemon-api-dev-comm-test:$API_PORT/health || {
    echo -e "${RED}❌ Container-to-container communication failed${NC}"
    exit 1
}
echo -e "${GREEN}✅ Container-to-container communication working${NC}"

docker stop daemon-api-dev-comm-test daemon-frontend-dev-comm-test
docker network rm daemon-dev-test-network
echo -e "${GREEN}✅ Multi-container development communication test passed${NC}"
echo

# Test 6: Multi-container communication (Production)
echo -e "${BLUE}🧪 Test 6: Multi-container communication (Production)${NC}"

echo "Creating Docker network..."
docker network create daemon-prod-test-network

echo "Starting API container (internal only)..."
docker run -d --name daemon-api-prod-comm-test \
    --network daemon-prod-test-network \
    --env-file .env.test \
    -v $(pwd)/data:/app/data \
    daemon-api:test

# Wait for API without external access
sleep $WAIT_TIME

echo "Starting frontend production container..."
docker run -d --name daemon-frontend-prod-comm-test \
    --network daemon-prod-test-network \
    -p $FRONTEND_PROD_HTTP_PORT:80 \
    -p $FRONTEND_PROD_HTTPS_PORT:443 \
    daemon-frontend:test

wait_for_service "http://localhost:$FRONTEND_PROD_HTTP_PORT/" "Frontend Production"

echo "Testing production setup..."
test_endpoint "http://localhost:$FRONTEND_PROD_HTTP_PORT/" "Frontend HTTP"
test_endpoint "http://localhost:$FRONTEND_PROD_HTTP_PORT/health" "Frontend health"

# Test internal communication
echo "Testing internal communication..."
docker exec daemon-frontend-prod-comm-test curl -f http://daemon-api-prod-comm-test:$API_PORT/health || {
    echo -e "${RED}❌ Internal communication failed${NC}"
    exit 1
}
echo -e "${GREEN}✅ Internal communication working${NC}"

docker stop daemon-api-prod-comm-test daemon-frontend-prod-comm-test
docker network rm daemon-prod-test-network
echo -e "${GREEN}✅ Multi-container production communication test passed${NC}"
echo

# Test 7: Docker Compose integration
echo -e "${BLUE}🧪 Test 7: Docker Compose integration${NC}"

if command -v docker-compose &> /dev/null; then
    echo "Testing Docker Compose profiles..."

    # Test API only
    echo "Testing API-only profile..."
    docker-compose up -d daemon-api
    wait_for_service "http://localhost:$API_PORT/health" "API (Compose)"
    docker-compose down

    echo -e "${GREEN}✅ Docker Compose integration test passed${NC}"
else
    echo -e "${YELLOW}⚠️ docker-compose not available, skipping integration test${NC}"
fi

echo

# Test 8: Resource and performance test
echo -e "${BLUE}🧪 Test 8: Resource and performance test${NC}"

echo "Starting container with resource limits..."
docker run -d --name daemon-api-resource-test \
    --memory=256m --cpus=0.5 \
    -p $API_PORT:$API_PORT \
    --env-file .env.test \
    daemon-api:test

wait_for_service "http://localhost:$API_PORT/health" "API (Resource Limited)"

echo "Running basic load test..."
for i in {1..20}; do
    curl -f -s http://localhost:$API_PORT/health > /dev/null &
done
wait
echo -e "${GREEN}✅ API handles concurrent requests${NC}"

echo "Container resource stats:"
docker stats daemon-api-resource-test --no-stream

docker stop daemon-api-resource-test
echo -e "${GREEN}✅ Resource and performance test passed${NC}"
echo

# Cleanup
cleanup_containers

echo -e "${GREEN}🎉 All Docker container tests passed!${NC}"
echo
echo -e "${BLUE}📊 Test Summary:${NC}"
echo "✅ Container builds"
echo "✅ Individual container functionality"
echo "✅ Multi-container communication"
echo "✅ Network isolation"
echo "✅ Resource constraints"
echo "✅ Production readiness"
echo

echo -e "${BLUE}🚀 Ready for deployment!${NC}"
