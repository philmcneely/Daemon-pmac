# Server Setup & Multi-App Hosting

This project supports flexible deployment options from simple development to complex multi-app hosting scenarios.

## � Quick Start

### Development (Simplest)
```bash
./scripts/dev-start.sh
```
- API: http://localhost:8004/
- Frontend: http://localhost:8005/
- Auto-reload enabled

### Production (Single App)
```bash
./scripts/prod-start.sh
```
- Uses .env configuration
- Validates security settings
- Production optimizations

### Multi-App Hosting
```bash
./scripts/multi-app-start.sh daemon 8004 8005
./scripts/multi-app-start.sh app2 8014 8015
./scripts/multi-app-start.sh app3 8024 8025
```

## 📁 Configuration Files

### Environment Variables (.env)
```bash
# Copy and customize
cp .env.example .env

# Key settings for multi-app hosting:
PORT=8004                    # API server port
FRONTEND_PORT=8005          # Frontend server port
DEPLOYMENT_MODE=production  # development, production, multi-app
EXTERNAL_DOMAIN=yourdomain.com
DAEMON_API_URL=https://yourdomain.com/daemon/api  # For path-based routing
```

### App-Specific Configuration
```bash
# .env.daemon - for daemon app
# .env.app2 - for second app
# .env.app3 - for third app
```

## 🌐 Multi-App Hosting Strategies

### Strategy 1: Path-Based (Recommended)
```
yourdomain.com/daemon/     → Daemon Frontend (port 8005)
yourdomain.com/daemon/api/ → Daemon API (port 8004)
yourdomain.com/app2/       → App2 Frontend (port 8015)
yourdomain.com/app2/api/   → App2 API (port 8014)
```

**Advantages:**
- Single SSL certificate
- Simple DNS setup
- Easy firewall rules

### Strategy 2: Subdomain-Based
```
daemon.yourdomain.com → Daemon Frontend (port 8005)
api.daemon.yourdomain.com → Daemon API (port 8004)
app2.yourdomain.com → App2 Frontend (port 8015)
api.app2.yourdomain.com → App2 API (port 8014)
```

**Advantages:**
- Clean separation
- Independent SSL certificates
- Easier app isolation

## 🔧 Port Management

### Recommended Port Allocation
```
Base: 8000-8099 (internal apps)

Daemon Portfolio:
- API: 8004, Frontend: 8005

App 2:
- API: 8014, Frontend: 8015

App 3:
- API: 8024, Frontend: 8025

Pattern: API = X4, Frontend = X5
```

### External Ports
```
80 (HTTP) → nginx → internal apps
443 (HTTPS) → nginx → internal apps
```

## 📋 Nginx Setup

### Path-Based Routing
```bash
# Copy example configuration
sudo cp nginx-multiapp.conf /etc/nginx/sites-available/daemon-multi
sudo ln -s /etc/nginx/sites-available/daemon-multi /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Subdomain-Based Routing
```bash
# Copy example configuration
sudo cp nginx-subdomains.conf /etc/nginx/sites-available/daemon-subdomains
sudo ln -s /etc/nginx/sites-available/daemon-subdomains /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 🔒 Security Best Practices

### Firewall Configuration
```bash
# Only expose nginx ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000:8099/tcp  # Block direct access to app ports
```

### App-Level Security
- Each app handles its own authentication
- Set unique SECRET_KEY per app
- Configure CORS for your domain
- Use SSL/TLS (terminate at nginx)

### Environment Security
```bash
# Secure .env files
chmod 600 .env*
# Add to .gitignore (already included)
```

## 🐳 Docker Deployment Options

Docker provides flexible deployment options - you can deploy just what you need:

### Option 1: API Only (Headless)
Perfect for API integrations, mobile apps, or when you have a custom frontend:
```bash
# Just the API
docker-compose up daemon-api

# Or with nginx reverse proxy
docker-compose --profile nginx up daemon-api nginx
```
- **API**: http://localhost:8004/ (or https via nginx)
- **Use cases**: Mobile apps, API integrations, custom frontends

### Option 2: Frontend Only
Deploy just the frontend if you have an external API:
```bash
# Frontend only (requires DAEMON_API_URL set to external API)
docker-compose --profile frontend up daemon-frontend
```
- **Frontend**: http://localhost:8005/
- **Use cases**: Frontend development, separate API hosting

### Option 3: Full Stack (API + Frontend)
Complete deployment with both components:
```bash
# Both API and frontend
docker-compose --profile frontend up daemon-api daemon-frontend

# With nginx reverse proxy
docker-compose --profile frontend --profile nginx up
```
- **Frontend**: http://localhost:8005/
- **API**: http://localhost:8004/
- **Nginx**: http://localhost/ (with path routing)

### Option 4: Production with Nginx
Full production setup with reverse proxy:
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  daemon-api:
    build: .
    environment:
      - PORT=8004
    expose:
      - "8004"
    # No direct port exposure - only through nginx

  daemon-frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    environment:
      - FRONTEND_PORT=8005
      - DAEMON_API_URL=http://daemon-api:8004
    expose:
      - "8005"
    # No direct port exposure - only through nginx

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-multiapp.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - daemon-api
      - daemon-frontend
```

### Environment Configuration
```bash
# .env file for Docker deployment
PORT=8004                    # API port
FRONTEND_PORT=8005          # Frontend port
DAEMON_API_URL=             # Auto-detected if not set
SECRET_KEY=your-secret-key
EXTERNAL_DOMAIN=yourdomain.com
```

## 🔄 Legacy Single-Server Mode

To revert to original single-server setup:
```bash
# In .env
PORT=8004

# Start
python -m uvicorn app.main:app --host 0.0.0.0 --port 8004
```

## 📊 Monitoring & Management

### Health Checks
```bash
# API Health
curl http://localhost:8004/health

# Frontend Health
curl -I http://localhost:8005/

# Through nginx
curl https://yourdomain.com/daemon/api/health
```

### Process Management
```bash
# View running apps
ls /tmp/daemon-apps/*.pid

# Stop specific app
kill $(cat /tmp/daemon-apps/daemon-api.pid)

# Stop all daemon processes
pkill -f "uvicorn.*app.main:app"
pkill -f "frontend_server.py"
```

## 🚨 Troubleshooting

### Port Conflicts
```bash
# Find what's using a port
lsof -i :8007

# Kill process on port
sudo kill -9 $(lsof -t -i:8007)
```

### CORS Issues
```bash
# Check CORS origins in .env
CORS_ORIGINS=["http://localhost:8006", "https://yourdomain.com"]

# Test API from frontend domain
curl -H "Origin: https://yourdomain.com" https://yourdomain.com/daemon/api/health
```

### SSL/TLS Issues
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check nginx configuration
sudo nginx -t
```
