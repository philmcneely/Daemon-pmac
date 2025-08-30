# Docker Deployment Examples

This document provides concrete examples for different Docker deployment scenarios.

## Quick Reference

| Deployment Type | Command | Ports | Use Case |
|----------------|---------|-------|----------|
| API Only | `docker-compose up daemon-api` | 8004 | Headless, mobile apps, custom frontends |
| Frontend Only | `docker-compose --profile frontend up daemon-frontend` | 8005 | Frontend dev against external API |
| Full Stack | `docker-compose --profile frontend up` | 8004, 8005 | Complete web application |
| Production | `docker-compose --profile frontend --profile nginx up` | 80, 443 | Production with reverse proxy |

## Detailed Examples

### 1. API Only Deployment

Perfect for:
- Mobile app backends
- API integrations
- Microservices architecture
- Custom frontend development

```bash
# Deploy just the API
docker-compose up daemon-api

# Test the API
curl http://localhost:8004/health
curl http://localhost:8004/api/v1/resume
```

### 2. Frontend Only Deployment

Perfect for:
- Frontend development
- Connecting to external APIs
- Testing UI changes

```bash
# Set external API URL
export DAEMON_API_URL=https://api.example.com

# Deploy just the frontend
docker-compose --profile frontend up daemon-frontend

# Access frontend
open http://localhost:8005
```

### 3. Full Stack Development

Perfect for:
- Complete local development
- Testing full application flow
- Demo environments

```bash
# Deploy both API and frontend
docker-compose --profile frontend up daemon-api daemon-frontend

# Access points:
# Frontend: http://localhost:8005
# API: http://localhost:8004
# API Docs: http://localhost:8004/docs
```

### 4. Production Deployment

Perfect for:
- Production hosting
- SSL termination
- Multiple domain hosting

```bash
# Complete production stack
docker-compose --profile frontend --profile nginx up

# Access points:
# Main site: http://localhost (or your domain)
# SSL: https://localhost (configure certificates)
```

## Environment Configuration

### .env Examples

#### Development (.env.dev)
```bash
# Development configuration
PORT=8004
FRONTEND_PORT=8005
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=["http://localhost:8005", "http://localhost:3000"]
DEBUG=true
```

#### Production (.env.prod)
```bash
# Production configuration
PORT=8004
FRONTEND_PORT=8005
SECRET_KEY=your-secure-production-secret
EXTERNAL_DOMAIN=yourdomain.com
CORS_ORIGINS=["https://yourdomain.com"]
DEBUG=false
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem
```

#### API-Only (.env.api)
```bash
# API-only configuration
PORT=8004
SECRET_KEY=api-secret-key
CORS_ORIGINS=["*"]  # Allow all origins for API-only
FRONTEND_ENABLED=false
```

## Advanced Scenarios

### Separate Networks

For enhanced security, run API and frontend on separate networks:

```yaml
# docker-compose.secure.yml
version: '3.8'

networks:
  backend:
    driver: bridge
    internal: true
  frontend:
    driver: bridge

services:
  daemon-api:
    build: .
    networks:
      - backend
    expose:
      - "8004"

  daemon-frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    networks:
      - frontend
      - backend
    ports:
      - "8005:8005"

  nginx:
    image: nginx:alpine
    networks:
      - frontend
    ports:
      - "80:80"
      - "443:443"
```

### Multi-Instance Deployment

Deploy multiple instances on different ports:

```bash
# Instance 1 - Main app
PORT=8004 FRONTEND_PORT=8005 docker-compose --profile frontend up -d

# Instance 2 - Testing
PORT=8014 FRONTEND_PORT=8015 docker-compose --profile frontend -f docker-compose.test.yml up -d

# Instance 3 - Staging
PORT=8024 FRONTEND_PORT=8025 docker-compose --profile frontend -f docker-compose.staging.yml up -d
```

### Database Persistence

Ensure data persistence across container restarts:

```yaml
services:
  daemon-api:
    build: .
    volumes:
      - daemon_data:/app/data
      - daemon_backups:/app/backups
      - daemon_logs:/app/logs

volumes:
  daemon_data:
    driver: local
  daemon_backups:
    driver: local
  daemon_logs:
    driver: local
```

## Health Checks

All containers include health checks:

```bash
# Check container health
docker-compose ps

# View health check logs
docker-compose logs daemon-api | grep health
docker-compose logs daemon-frontend | grep health
```

## Troubleshooting

### Port Conflicts
```bash
# Check what's using a port
lsof -i :8004

# Use different ports
PORT=8014 FRONTEND_PORT=8015 docker-compose up
```

### CORS Issues
```bash
# Allow specific origins
CORS_ORIGINS='["http://localhost:8005", "https://yourdomain.com"]' docker-compose up

# Allow all origins (development only)
CORS_ORIGINS='["*"]' docker-compose up
```

### Container Communication
```bash
# Test API from frontend container
docker-compose exec daemon-frontend curl http://daemon-api:8004/health

# Test external access
curl http://localhost:8004/health
```

This flexible approach means users can start simple (API-only) and add components as needed, or deploy only what they require for their specific use case.
