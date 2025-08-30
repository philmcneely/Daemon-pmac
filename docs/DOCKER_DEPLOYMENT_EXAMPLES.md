# Docker Deployment Examples

This document provides concrete examples for different Docker deployment scenarios.

## Quick Reference

| Deployment Type | Command | Ports | Use Case |
|----------------|---------|-------|----------|
| API Only | `docker-compose up daemon-api` | 8004 | Headless, mobile apps, custom frontends |
| Frontend Dev | `docker-compose --profile frontend-dev up` | 8005 | Frontend development with Python server |
| Frontend Prod | `docker-compose --profile frontend up` | 80, 443 | Production with nginx + SSL |
| Full Dev Stack | `docker-compose --profile frontend-dev up` | 8004, 8005 | Complete development environment |
| Full Production | `docker-compose -f docker-compose.prod.yml up` | 80, 443 | Enterprise production deployment |

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

### 2. Frontend Development

Perfect for:
- Frontend development with hot reload
- Testing UI changes
- Development against local or remote API

```bash
# Development frontend (Python server)
docker-compose --profile frontend-dev up daemon-frontend-dev

# Access frontend
open http://localhost:8005
```

### 3. Frontend Production

Perfect for:
- Production deployments
- SSL/HTTPS support
- High-performance static file serving

```bash
# Production frontend (nginx + SSL)
docker-compose --profile frontend up daemon-frontend

# Access frontend
open https://localhost  # or http://localhost (redirects to HTTPS)
```

### 4. Full Stack Development

Perfect for:
- Complete local development
- Testing full application flow
- Demo environments

```bash
# Deploy both API and frontend (development)
docker-compose --profile frontend-dev up

# Access points:
# Frontend: http://localhost:8005 (Python server)
# API: http://localhost:8004
# API Docs: http://localhost:8004/docs
```

### 5. Full Production Deployment

Perfect for:
- Production hosting
- SSL termination
- Enterprise-grade security

```bash
# Setup SSL certificates first
./scripts/setup-ssl.sh

# Complete production stack
docker-compose -f docker-compose.prod.yml up -d

# Access points:
# Main site: https://yourdomain.com
# Health check: https://yourdomain.com/health
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

## Production Deployment Guide

### SSL Certificate Setup

#### Development (Self-Signed)
```bash
# Generate self-signed certificates
./scripts/setup-ssl.sh
# Choose option 1: Generate self-signed certificate

# Certificates will be created in ./ssl/
```

#### Production (Let's Encrypt)
```bash
# Set your domain
export DOMAIN=yourdomain.com

# Generate production certificates
./scripts/setup-ssl.sh
# Choose option 2: Setup Let's Encrypt certificate
```

#### Production (Custom Certificates)
```bash
# Place your certificates in ./ssl/
cp your-cert.pem ./ssl/cert.pem
cp your-key.pem ./ssl/key.pem

# Validate certificates
./scripts/setup-ssl.sh
# Choose option 3: Validate existing certificates
```

### Production Environment Configuration

Create a production environment file:

```bash
# .env.prod
SECRET_KEY=your-super-secure-production-secret-key-here
DOMAIN=yourdomain.com
PORT=8004
DEBUG=false

# SSL Configuration
SSL_CERT_PATH=./ssl/cert.pem
SSL_KEY_PATH=./ssl/key.pem

# Security Settings
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com"]

# Database (for production, consider external database)
DATABASE_URL=sqlite:///./data/daemon.db
BACKUP_DIR=./backups

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### Production Deployment Steps

1. **Prepare the environment:**
```bash
# Clone repository
git clone https://github.com/philmcneely/Daemon-pmac.git
cd Daemon-pmac

# Create production environment
cp .env.example .env.prod
# Edit .env.prod with your settings
```

2. **Setup SSL:**
```bash
# For Let's Encrypt
export DOMAIN=yourdomain.com
./scripts/setup-ssl.sh

# Or place custom certificates in ./ssl/
```

3. **Deploy:**
```bash
# Build and start production containers
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

4. **Verify deployment:**
```bash
# Test HTTPS endpoint
curl -I https://yourdomain.com/health

# Check API
curl https://yourdomain.com/api/v1/system/info
```

### Production Security Features

The production frontend container includes:

- **nginx with SSL/TLS termination**
- **HTTP to HTTPS redirects**
- **Security headers (HSTS, CSP, etc.)**
- **Rate limiting for API endpoints**
- **Static file optimization and caching**
- **Gzip compression**
- **Non-root user execution**
- **Health checks and monitoring**

### Monitoring and Maintenance

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Update containers
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Backup data
docker-compose -f docker-compose.prod.yml exec daemon-api python -m app.cli backup

# Certificate renewal (Let's Encrypt)
sudo certbot renew
./scripts/setup-ssl.sh  # Choose option 3 to copy new certificates
docker-compose -f docker-compose.prod.yml restart daemon-frontend
```

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
