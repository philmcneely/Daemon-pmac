# Docker Container Testing Documentation

This document describes the comprehensive testing strategy for Docker containers in the Daemon project, covering individual container validation and multi-container communication testing.

## Testing Overview

The Docker testing suite validates:

1. **Individual Container Functionality** - Each container works standalone
2. **Multi-Container Communication** - Containers communicate properly
3. **Network Isolation** - Production security boundaries work
4. **Docker Compose Integration** - All deployment profiles function
5. **Resource Management** - Containers respect resource limits
6. **Production Readiness** - SSL, security headers, and performance

## Test Environments

### CI Environment (GitHub Actions)

The CI pipeline runs comprehensive Docker tests automatically on every push and pull request:

```yaml
# .github/workflows/ci.yml
jobs:
  docker:
    name: Docker Container Tests
    runs-on: ubuntu-latest
    needs: [test, lint]
```

**CI Test Sequence:**
1. Build all container variants
2. Test each container individually
3. Test multi-container communication
4. Test Docker Compose profiles
5. Validate production deployment
6. Push to Docker Hub (on main branch)

### Local Development

Run tests locally for development and debugging:

```bash
# Run complete test suite
./scripts/test-docker.sh

# Run with custom configuration
API_PORT=8014 FRONTEND_DEV_PORT=8015 ./scripts/test-docker.sh

# Run without cleanup (for debugging)
CLEANUP=false ./scripts/test-docker.sh
```

## Test Cases

### 1. Container Build Tests

**Purpose:** Verify all Docker images build successfully

**Containers Tested:**
- `daemon-api:test` - Main API server
- `daemon-frontend-dev:test` - Development frontend (Python server)
- `daemon-frontend:test` - Production frontend (nginx + SSL)

**Validation:**
- ✅ All builds complete without errors
- ✅ Images are created and tagged correctly
- ✅ Multi-platform support (linux/amd64, linux/arm64)

### 2. API Container Standalone Test

**Purpose:** Validate API container works independently

**Test Steps:**
1. Start API container with test configuration
2. Wait for health check to pass
3. Test core endpoints:
   - `/health` - Health check endpoint
   - `/docs` - API documentation
   - `/api/v1/system/info` - System information

**Expected Results:**
- ✅ Container starts within timeout period
- ✅ All endpoints return successful responses
- ✅ Database initialization completes
- ✅ Logging and monitoring work

### 3. Frontend Development Container Test

**Purpose:** Validate development frontend container

**Test Steps:**
1. Start frontend development container (Python server)
2. Test accessibility and basic functionality
3. Verify development-specific features

**Expected Results:**
- ✅ Python server starts on configured port
- ✅ Static files serve correctly
- ✅ Development server provides proper responses

### 4. Frontend Production Container Test

**Purpose:** Validate production frontend with nginx

**Test Steps:**
1. Start production frontend container
2. Test HTTP and HTTPS endpoints
3. Verify security headers and SSL configuration
4. Test health check endpoint

**Expected Results:**
- ✅ nginx starts and serves content
- ✅ HTTP automatically redirects to HTTPS
- ✅ Self-signed SSL certificates work
- ✅ Security headers are present
- ✅ Gzip compression is enabled
- ✅ Static file caching works

### 5. Multi-Container Communication (Development)

**Purpose:** Test container-to-container communication in development mode

**Architecture:**
```
Host Network (8004, 8005)
    ↓
Docker Network (daemon-dev-test-network)
    ├── daemon-api-dev-comm-test:8004
    └── daemon-frontend-dev-comm-test:8005
```

**Test Steps:**
1. Create isolated Docker network
2. Start API container on network
3. Start frontend development container on network
4. Test external accessibility from host
5. Test internal container-to-container communication

**Expected Results:**
- ✅ Both containers accessible from host
- ✅ Frontend can communicate with API internally
- ✅ API data flows correctly to frontend
- ✅ Network isolation maintained

### 6. Multi-Container Communication (Production)

**Purpose:** Test production deployment with network isolation

**Architecture:**
```
Host Network (80, 443)
    ↓
nginx (daemon-frontend-prod-comm-test)
    ↓
Internal Network
    └── daemon-api-prod-comm-test:8004 (internal only)
```

**Test Steps:**
1. Create production network topology
2. Start API container (internal access only)
3. Start nginx frontend container
4. Test external HTTPS access
5. Verify API is not externally accessible
6. Test internal API communication through nginx

**Expected Results:**
- ✅ Frontend accessible via HTTP/HTTPS
- ✅ API not directly accessible from host
- ✅ Internal communication works
- ✅ SSL termination functions correctly
- ✅ Security boundaries maintained

### 7. Docker Compose Profile Tests

**Purpose:** Validate all Docker Compose deployment profiles

**Profiles Tested:**
- **API Only:** `docker-compose up daemon-api`
- **Development:** `docker-compose --profile frontend-dev up`
- **Production:** `docker-compose --profile frontend up`

**Test Steps:**
1. Test each profile independently
2. Verify services start correctly
3. Test inter-service communication
4. Clean shutdown and cleanup

**Expected Results:**
- ✅ All profiles deploy successfully
- ✅ Services communicate as designed
- ✅ Port mappings work correctly
- ✅ Environment variables propagate

### 8. Resource and Performance Tests

**Purpose:** Validate containers work under resource constraints

**Test Configuration:**
- Memory limit: 256MB
- CPU limit: 0.5 cores
- Concurrent request testing

**Test Steps:**
1. Start containers with resource limits
2. Verify normal operation under constraints
3. Generate concurrent load
4. Monitor resource usage
5. Validate performance benchmarks

**Expected Results:**
- ✅ Containers respect resource limits
- ✅ Performance remains acceptable
- ✅ No memory leaks or resource issues
- ✅ Graceful handling of load spikes

## Failure Scenarios Tested

### Network Failures
- Container network isolation
- DNS resolution between containers
- Port conflict detection

### Security Validations
- Non-root user execution
- SSL certificate validation
- Security header presence
- CORS configuration

### Resource Constraints
- Memory limit enforcement
- CPU throttling behavior
- Disk space management

## Test Output and Debugging

### Successful Test Output
```bash
🐳 Docker Container Test Suite
==============================================
🏗️ Test 1: Building all containers
✅ All containers built successfully

🧪 Test 2: API container standalone
✅ API container standalone test passed

🧪 Test 3: Frontend development container standalone
✅ Frontend development container standalone test passed

🧪 Test 4: Frontend production container standalone
✅ Frontend production container standalone test passed

🧪 Test 5: Multi-container communication (Development)
✅ Multi-container development communication test passed

🧪 Test 6: Multi-container communication (Production)
✅ Multi-container production communication test passed

🧪 Test 7: Docker Compose integration
✅ Docker Compose integration test passed

🧪 Test 8: Resource and performance test
✅ Resource and performance test passed

🎉 All Docker container tests passed!
```

### Debugging Failed Tests

If tests fail, use these debugging approaches:

```bash
# Run without cleanup to inspect containers
CLEANUP=false ./scripts/test-docker.sh

# Check container logs
docker logs daemon-api-standalone-test

# Inspect container configuration
docker inspect daemon-frontend-prod-standalone-test

# Test endpoints manually
curl -v http://localhost:8004/health

# Check container resources
docker stats --no-stream
```

### Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Port conflicts | Container fails to start | Change ports with environment variables |
| SSL certificate issues | HTTPS requests fail | Check certificate generation in container |
| Network connectivity | Containers can't communicate | Verify Docker network configuration |
| Resource constraints | Container killed/restarts | Increase memory/CPU limits |
| Startup timeouts | Health checks fail | Increase `WAIT_TIME` environment variable |

## Integration with CI/CD

### GitHub Actions Integration

The Docker tests are integrated into the CI/CD pipeline:

1. **Trigger:** Every push and pull request
2. **Dependencies:** Runs after unit tests and linting pass
3. **Parallelization:** Tests run independently where possible
4. **Caching:** Docker layer caching for faster builds
5. **Artifacts:** Test results and container images published

### Pull Request Validation

For pull requests, the pipeline:
- Builds and tests all containers
- Validates multi-container communication
- Ensures no regressions in deployment profiles
- Provides detailed test results in PR comments

### Production Deployment

For main branch pushes:
- Complete test suite must pass
- Containers are built for multiple platforms
- Images are pushed to Docker Hub
- Production deployment can proceed

## Local Development Workflow

### Testing Changes

```bash
# 1. Make Docker-related changes
vim Dockerfile frontend/Dockerfile

# 2. Test locally
./scripts/test-docker.sh

# 3. Fix any issues and re-test
# 4. Commit and push (CI will run full test suite)
```

### Debugging Container Issues

```bash
# Build and run specific container for debugging
docker build -t debug-api .
docker run -it --entrypoint /bin/bash debug-api

# Test specific communication scenarios
docker network create debug-net
docker run -d --network debug-net --name api debug-api
docker run -it --network debug-net alpine/curl curl http://api:8004/health
```

This comprehensive testing approach ensures that Docker containers work reliably both individually and as part of the complete multi-container application stack.
