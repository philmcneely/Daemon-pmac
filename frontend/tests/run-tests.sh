#!/bin/bash

# Frontend E2E Test Runner
# Comprehensive test execution script for Daemon Portfolio Frontend

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_PORT=${FRONTEND_PORT:-8006}
API_PORT=${API_PORT:-8007}
TEST_TIMEOUT=${TEST_TIMEOUT:-60000}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Frontend E2E Test Runner

Usage: $0 [OPTIONS] [TEST_SUITE]

OPTIONS:
    -h, --help          Show this help message
    -p, --port PORT     Frontend server port (default: 8006)
    -a, --api-port PORT API server port (default: 8007)
    -t, --timeout MS    Test timeout in milliseconds (default: 60000)
    -H, --headed        Run tests in headed mode (visible browser)
    -d, --debug         Run tests in debug mode
    -r, --report        Generate and open HTML report
    -c, --ci            Run in CI mode (no interactive features)
    --setup-only        Only setup servers, don't run tests
    --cleanup-only      Only cleanup processes

TEST_SUITES:
    single-user         Run single-user mode tests only
    multi-user          Run multi-user mode tests only
    api-integration     Run API integration tests only
    performance         Run performance tests only
    accessibility       Run accessibility tests only
    all                 Run all test suites (default)

EXAMPLES:
    $0                          # Run all tests
    $0 single-user             # Run only single-user tests
    $0 --headed multi-user     # Run multi-user tests with visible browser
    $0 --debug api-integration # Debug API integration tests
    $0 --ci --report           # Run all tests in CI mode with report

EOF
}

# Parse command line arguments
HEADED=false
DEBUG=false
REPORT=false
CI_MODE=false
SETUP_ONLY=false
CLEANUP_ONLY=false
TEST_SUITE="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        -a|--api-port)
            API_PORT="$2"
            shift 2
            ;;
        -t|--timeout)
            TEST_TIMEOUT="$2"
            shift 2
            ;;
        -H|--headed)
            HEADED=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -r|--report)
            REPORT=true
            shift
            ;;
        -c|--ci)
            CI_MODE=true
            shift
            ;;
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --cleanup-only)
            CLEANUP_ONLY=true
            shift
            ;;
        single-user|multi-user|api-integration|performance|accessibility|all)
            TEST_SUITE="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Process IDs for cleanup
API_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    log_info "Cleaning up processes..."

    if [[ -n "$FRONTEND_PID" ]]; then
        log_info "Stopping frontend server (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    if [[ -n "$API_PID" ]]; then
        log_info "Stopping API server (PID: $API_PID)"
        kill $API_PID 2>/dev/null || true
    fi

    # Kill any remaining servers on the ports
    pkill -f "uvicorn.*:$API_PORT" 2>/dev/null || true
    pkill -f "frontend_server.*$FRONTEND_PORT" 2>/dev/null || true

    log_success "Cleanup complete"
}

# Handle cleanup only mode
if [[ "$CLEANUP_ONLY" == "true" ]]; then
    cleanup
    exit 0
fi

# Set trap for cleanup
trap cleanup EXIT

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi

    # Check if in test directory
    if [[ ! -f "$SCRIPT_DIR/package.json" ]]; then
        log_error "Must be run from frontend/tests directory"
        exit 1
    fi

    # Install npm dependencies if needed
    if [[ ! -d "$SCRIPT_DIR/node_modules" ]]; then
        log_info "Installing npm dependencies..."
        cd "$SCRIPT_DIR"
        npm install
    fi

    # Check Playwright installation
    if ! npx playwright --version &> /dev/null; then
        log_info "Installing Playwright browsers..."
        npx playwright install
    fi

    log_success "Dependencies check complete"
}

# Setup database
setup_database() {
    log_info "Setting up test database..."
    cd "$PROJECT_ROOT"

    # Create test database
    python3 -c "
from app.database import init_db
init_db()
print('Database initialized')
    " || {
        log_error "Failed to initialize database"
        exit 1
    }

    log_success "Database setup complete"
}

# Start API server
start_api_server() {
    log_info "Starting API server on port $API_PORT..."
    cd "$PROJECT_ROOT"

    # Check if port is available
    if lsof -i :$API_PORT &> /dev/null; then
        log_warning "Port $API_PORT is already in use"
        if [[ "$CI_MODE" == "false" ]]; then
            read -p "Kill existing process and continue? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
        pkill -f "uvicorn.*:$API_PORT" 2>/dev/null || true
        sleep 2
    fi

    # Start API server in background
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port $API_PORT &
    API_PID=$!

    # Wait for server to start
    log_info "Waiting for API server to start..."
    for i in {1..30}; do
        if curl -f "http://localhost:$API_PORT/health" &> /dev/null; then
            log_success "API server started successfully"
            return 0
        fi
        sleep 1
    done

    log_error "API server failed to start"
    exit 1
}

# Start frontend server
start_frontend_server() {
    log_info "Starting frontend server on port $FRONTEND_PORT..."
    cd "$PROJECT_ROOT"

    # Check if port is available
    if lsof -i :$FRONTEND_PORT &> /dev/null; then
        log_warning "Port $FRONTEND_PORT is already in use"
        if [[ "$CI_MODE" == "false" ]]; then
            read -p "Kill existing process and continue? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
        pkill -f "frontend_server.*$FRONTEND_PORT" 2>/dev/null || true
        sleep 2
    fi

    # Start frontend server in background
    FRONTEND_PORT=$FRONTEND_PORT python3 frontend_server.py &
    FRONTEND_PID=$!

    # Wait for server to start
    log_info "Waiting for frontend server to start..."
    for i in {1..15}; do
        if curl -f "http://localhost:$FRONTEND_PORT/" &> /dev/null; then
            log_success "Frontend server started successfully"
            return 0
        fi
        sleep 1
    done

    log_error "Frontend server failed to start"
    exit 1
}

# Run tests
run_tests() {
    log_info "Running E2E tests (suite: $TEST_SUITE)..."
    cd "$SCRIPT_DIR"

    # Build test command
    local test_cmd="npx playwright test"

    # Add test suite filter
    if [[ "$TEST_SUITE" != "all" ]]; then
        test_cmd="$test_cmd $TEST_SUITE"
    fi

    # Add options
    if [[ "$HEADED" == "true" ]]; then
        test_cmd="$test_cmd --headed"
    fi

    if [[ "$DEBUG" == "true" ]]; then
        test_cmd="$test_cmd --debug"
    fi

    if [[ "$CI_MODE" == "true" ]]; then
        test_cmd="$test_cmd --reporter=github,html"
    fi

    # Set environment variables
    export CI=$CI_MODE
    export FRONTEND_PORT=$FRONTEND_PORT
    export API_PORT=$API_PORT
    export TEST_TIMEOUT=$TEST_TIMEOUT

    # Run tests
    log_info "Executing: $test_cmd"
    if $test_cmd; then
        log_success "All tests passed!"
        TEST_RESULT=0
    else
        log_error "Some tests failed"
        TEST_RESULT=1
    fi

    # Generate report if requested
    if [[ "$REPORT" == "true" && -d "playwright-report" ]]; then
        log_info "Opening test report..."
        npx playwright show-report
    fi

    return $TEST_RESULT
}

# Main execution
main() {
    log_info "Starting Frontend E2E Test Runner"
    log_info "Configuration: Frontend Port: $FRONTEND_PORT, API Port: $API_PORT"
    log_info "Test Suite: $TEST_SUITE, Headed: $HEADED, Debug: $DEBUG, CI: $CI_MODE"

    # Check dependencies
    check_dependencies

    # Setup database
    setup_database

    # Start servers
    start_api_server
    start_frontend_server

    # Handle setup-only mode
    if [[ "$SETUP_ONLY" == "true" ]]; then
        log_success "Servers started successfully"
        log_info "API Server: http://localhost:$API_PORT"
        log_info "Frontend Server: http://localhost:$FRONTEND_PORT"
        log_info "Press Ctrl+C to stop servers"

        # Wait indefinitely
        while true; do
            sleep 1
        done
    fi

    # Run tests
    run_tests
    local test_result=$?

    if [[ $test_result -eq 0 ]]; then
        log_success "E2E test run completed successfully!"
    else
        log_error "E2E test run completed with failures"
    fi

    return $test_result
}

# Execute main function
main "$@"
