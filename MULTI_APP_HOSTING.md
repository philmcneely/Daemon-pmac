# Multi-App Hosting Configuration

## Overview
This document outlines how to configure the Daemon portfolio for multi-app hosting scenarios where you want to run multiple applications behind a reverse proxy.

## Configuration Approach

### Environment Variables
The application now supports full environment-based configuration:

```bash
# API Server Configuration
DAEMON_API_HOST=0.0.0.0
DAEMON_API_PORT=8007
DAEMON_API_BASE_PATH=/daemon/api

# Frontend Configuration
DAEMON_FRONTEND_HOST=0.0.0.0
DAEMON_FRONTEND_PORT=8006
DAEMON_FRONTEND_BASE_PATH=/daemon

# Database
DAEMON_DATABASE_URL=sqlite:///./daemon.db

# Security
DAEMON_SECRET_KEY=your-secret-key-here
DAEMON_CORS_ORIGINS=http://localhost,https://yourdomain.com
```

## Multi-App Hosting Scenarios

### Scenario 1: Single Server, Multiple Apps
```
nginx (port 80/443)
├── /daemon/     → Daemon Frontend (port 8006)
├── /daemon/api/ → Daemon API (port 8007)
├── /app2/       → App2 Frontend (port 8008)
├── /app2/api/   → App2 API (port 8009)
└── /app3/       → App3 Frontend (port 8010)
    /app3/api/   → App3 API (port 8011)
```

### Scenario 2: Subdomain-Based
```
nginx (port 80/443)
├── daemon.yourdomain.com → Daemon Frontend (port 8006)
├── api.daemon.yourdomain.com → Daemon API (port 8007)
├── app2.yourdomain.com → App2 Frontend (port 8008)
└── api.app2.yourdomain.com → App2 API (port 8009)
```

## Quick Setup Scripts

### Development (Local)
```bash
./scripts/dev-start.sh
```

### Production (Single App)
```bash
./scripts/prod-start.sh
```

### Production (Multi-App with nginx)
```bash
./scripts/multi-app-start.sh daemon
```

## Nginx Configuration Examples

### Path-Based Routing
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Daemon Portfolio
    location /daemon/api/ {
        proxy_pass http://localhost:8007/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /daemon/ {
        proxy_pass http://localhost:8006/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Other apps...
    location /app2/api/ {
        proxy_pass http://localhost:8009/;
    }

    location /app2/ {
        proxy_pass http://localhost:8008/;
    }
}
```

### Subdomain-Based Routing
```nginx
# Daemon API
server {
    listen 80;
    server_name api.daemon.yourdomain.com;

    location / {
        proxy_pass http://localhost:8007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Daemon Frontend
server {
    listen 80;
    server_name daemon.yourdomain.com;

    location / {
        proxy_pass http://localhost:8006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Port Management Strategy

### Recommended Port Allocation
```
Base Port Range: 8000-8099

App 1 (Daemon):
- API: 8007
- Frontend: 8006

App 2:
- API: 8017
- Frontend: 8016

App 3:
- API: 8027
- Frontend: 8026
```

This leaves room for 10 apps with clear port patterns.

## Security Considerations

1. **Firewall**: Only expose nginx ports (80/443) externally
2. **Internal Apps**: Bind to localhost or internal network only
3. **Authentication**: Each app handles its own auth
4. **CORS**: Configure for your external domain
5. **SSL**: Terminate SSL at nginx level

## Docker Option (Alternative)

For even cleaner multi-app hosting, consider:
```yaml
# docker-compose.yml
version: '3.8'
services:
  daemon-api:
    build: .
    environment:
      - DAEMON_API_PORT=8007
      - DAEMON_API_BASE_PATH=/daemon/api
    ports:
      - "8007:8007"

  daemon-frontend:
    build: ./frontend
    environment:
      - DAEMON_FRONTEND_PORT=8006
      - DAEMON_API_URL=http://daemon-api:8007
    ports:
      - "8006:8006"

  nginx:
    image: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```
