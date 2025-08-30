# Daemon: Multi-User Personal API Framework

## 🤖 CRITICAL COPILOT RULES (MANDATORY)

**⚠️ DEVELOPMENT WORKFLOW - NEVER VIOLATE THESE RULES:**

### Test-First Development
- **ALWAYS** update tests when changing functionality
- **ALWAYS** run tests and ensure they pass before proceeding
- **NEVER** move to next task until all tests pass and docs are updated

### Documentation Updates
- **ALWAYS** update `API_REQUIREMENTS.md` when changing API behavior
- **ALWAYS** update `E2E_TEST_CASES_GIVEN_WHEN_THEN.md` for new test scenarios
- **ALWAYS** update OpenAPI documentation for endpoint changes

### Command Output Handling
- **ALWAYS** pipe GitHub CLI (`gh`) commands to files in `gh_temp/` directory first, then read the file
- **ALWAYS** pipe `curl` commands to files in `gh_temp/` directory first, then read the file
- **NEVER** try to read CLI output directly from terminal

### File Management
- **NEVER** create extraneous files for one-offs in the root directory
- **NEVER** create duplicate files and leave them around
- **ALWAYS** clean up temporary files after use
- **ALWAYS** use `gh_temp/` directory for temporary files (it's gitignored)

### Check Existing Before Creating New
- **ALWAYS** check what endpoints, functions, or features already exist before creating new ones
- **NEVER** create duplicate functionality without understanding why existing solutions don't work
- **ALWAYS** search codebase for similar functionality before implementing from scratch
- **ALWAYS** use `grep_search`, `semantic_search`, or `file_search` to find existing implementations

### Problem Resolution
- **NEVER** suppress warnings or add workarounds - ALWAYS fix the root cause
- **ALWAYS** examine application code first to understand how to perform actions correctly

### Work Completion
- **ALWAYS** commit changes before summarizing what you've done

### Quality Gates (ALL MUST PASS)
- ✅ All existing tests must pass
- ✅ New tests must pass
- ✅ Documentation must be updated and accurate
- ✅ OpenAPI schema must be current
- ✅ No temporary files in project root

---

[![CI/CD Pipeline](https://github.com/philmcneely/Daemon-pmac/actions/workflows/ci.yml/badge.svg)](https://github.com/philmcneely/Daemon-pmac/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/philmcneely/Daemon-pmac/branch/main/graph/badge.svg)](https://codecov.io/gh/philmcneely/Daemon-pmac)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **adaptive personal API framework** that seamlessly scales from single-user simplicity to multi-user complexity with comprehensive privacy controls. Built with FastAPI and inspired by [Daniel Miessler's Daemon project](https://github.com/danielmiessler/Daemon).

> **Adaptive Design**: Automatically switches between single-user mode (simple `/api/v1/resume`) and multi-user mode (`/api/v1/resume/users/pmac`) based on the number of users in the system.

## ✨ Key Features

### 🔄 **Adaptive Multi-User Support**
- **Single User (≤1 user)**: Clean, simple endpoints without usernames
- **Multi-User (2+ users)**: User-specific endpoints with full data isolation
- **Automatic Mode Detection**: Seamlessly transitions between modes

### 🔐 **Advanced Privacy System**
- **Configurable Privacy Levels**: `business_card`, `professional`, `public_full`, `ai_safe`
- **Smart Data Filtering**: Automatically removes sensitive information (phone, SSN, salary, etc.)
- **User-Controlled Settings**: Each user controls their own privacy preferences
- **AI-Safe Mode**: Perfect for AI assistant access with automatic data sanitization

### 🚀 **Production Ready**
- **FastAPI-based**: High-performance async API with auto-generated docs
- **Secure by default**: JWT authentication, rate limiting, input validation
- **SQLite database**: Lightweight with automatic backups and audit logging
- **Docker support**: Easy deployment anywhere
- **Health monitoring**: Comprehensive health checks and metrics

### 🎯 **Developer Friendly**
- **Hot reload**: Development-friendly with automatic reloading
- **CLI tools**: Easy user and data management commands
- **Extensible**: Simple to add new endpoints and data types
- **RESTful design**: Clean, predictable API patterns

## 🚀 Quick Start

### Installation

```bash
# Clone and setup
git clone <your-repo-url>
cd daemon-pmac

# Create and activate virtual environment (RECOMMENDED)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create first user (becomes admin automatically)
python -m app.cli create-user pmac

# Start the server
python dev.py
```

### Development Setup

For development work, use the automated setup script:

```bash
# Quick setup with virtual environment and pre-commit hooks
chmod +x setup-dev.sh
./setup-dev.sh
```

This script will:
- Create a Python virtual environment (`venv/`)
- Install all dependencies
- Set up pre-commit hooks for code quality
- Initialize database and directories

**VS Code Integration**: Open the project with:
```bash
code daemon-pmac.code-workspace
```

#### Manual Development Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks (RECOMMENDED)
pre-commit install

# Run tests
pytest tests/

# Manual formatting and linting
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/

# Run security checks
bandit -r app/
safety check
pip-audit
```

### 🚀 Deployment Options

#### Quick Development Server
```bash
# Using new deployment scripts (recommended)
./scripts/dev-start.sh        # Development with hot reload
./scripts/prod-start.sh       # Production single-app mode

# Legacy method
python dev.py                 # Single server on port 8004
```

#### Multi-App Hosting
Perfect for hosting multiple applications on one server:
```bash
# Start individual apps on specific ports
./scripts/multi-app-start.sh daemon 8004 8005
./scripts/multi-app-start.sh app2 8014 8015
./scripts/multi-app-start.sh app3 8024 8025

# Configure nginx for reverse proxy (see docs/SERVER_SETUP.md)
```

#### Environment Configuration
```bash
# Copy and customize environment settings
cp .env.example .env
# Edit .env with your specific ports and domain settings

# Key settings for multi-app hosting:
PORT=8007                    # API server port
FRONTEND_PORT=8006          # Frontend server port
DEPLOYMENT_MODE=production  # development, production, multi-app
EXTERNAL_DOMAIN=yourdomain.com
```

For comprehensive deployment documentation, see:
- **[Server Setup Guide](docs/SERVER_SETUP.md)** - Single and multi-server configurations
- **[Multi-App Hosting](docs/MULTI_APP_HOSTING.md)** - nginx, Docker, and production hosting

#### Pre-commit Hooks

This project uses **pre-commit hooks** to ensure code quality before commits:

- **Black**: Automatic Python code formatting
- **isort**: Import statement sorting
- **Trailing whitespace**: Removes trailing spaces
- **End of file**: Ensures files end with newline
- **YAML/JSON validation**: Syntax checking for config files

The hooks run automatically before each commit and **prevent** the code quality failures that would otherwise break the CI/CD pipeline.

```bash
# Test all hooks manually
pre-commit run --all-files

# Skip hooks for a specific commit (not recommended)
git commit --no-verify -m "emergency fix"
```

### CI/CD

The project includes comprehensive GitHub Actions workflows:

- **Tests**: Automated testing across Python 3.9-3.12
- **Code Quality**: Black, isort, flake8, mypy linting
- **Security**: Bandit security scanning and dependency audits
- **Auto-formatting**: Automatic code formatting on push
- **Dependency Updates**: Weekly automated dependency updates
- **Docker**: Multi-platform container builds
- **Deployment**: Automated staging and production deployments

Configure these GitHub secrets for full CI/CD:
- `DOCKER_USERNAME` and `DOCKER_PASSWORD` for Docker Hub
- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY` for staging deployment
- `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY` for production deployment
- `SLACK_WEBHOOK_URL` for deployment notifications

### Single User Mode (1 user)
```bash
# Simple, clean endpoints (default port 8004)
curl "http://localhost:8004/api/v1/resume"
curl "http://localhost:8004/api/v1/skills"
curl "http://localhost:8004/api/v1/hobbies"
```

### Multi-User Mode (2+ users)
```bash
# Create second user (triggers multi-user mode)
python -m app.cli create-user kime

# User-specific endpoints with privacy levels
curl "http://localhost:8004/api/v1/resume/users/pmac?level=ai_safe"
curl "http://localhost:8004/api/v1/skills/users/kime?level=business_card"
```

## 📚 API Examples

### System Information
```bash
GET /api/v1/system/info
# Returns current mode and endpoint patterns
```

### Privacy Levels
```bash
# Ultra-minimal business card view
GET /api/v1/resume/users/pmac?level=business_card

# Professional networking view
GET /api/v1/resume/users/pmac?level=professional

# Full public view (respects user privacy settings)
GET /api/v1/resume/users/pmac?level=public_full

# AI assistant safe view (no sensitive data)
GET /api/v1/resume/users/pmac?level=ai_safe
```

### User Management
```bash
# Register new user
POST /auth/register
{
  "username": "pmac",
  "email": "phil@pmac.dev",
  "password": "secure_password"
}

# Complete user setup (admin only)
POST /api/v1/setup/user/kime
{
  "username": "kime",
  "email": "kime@example.com",
  "password": "secure_password"
}
```

## 🔐 Privacy & Security

### Privacy Filtering
The system automatically filters sensitive data for public access:

**Original Data:**
```json
{
  "name": "Phil McNeely",
  "contact": {
    "email": "phil@pmac.dev",
    "phone": "+1-555-123-4567",
    "personal_email": "personal@gmail.com"
  },
  "salary": 150000
}
```

**Public Filtered (`ai_safe` level):**
```json
{
  "name": "Phil McNeely",
  "contact": {
    "email": "phil@pmac.dev"
  }
}
```

### Privacy Settings
Users control their own privacy:
```bash
# Update privacy settings
PUT /api/v1/privacy/settings
{
  "business_card_mode": false,
  "ai_assistant_access": true,
  "show_contact_info": true,
  "custom_privacy_rules": {"contact.phone": "hide"}
}

# Preview privacy filtering
GET /api/v1/privacy/preview/resume?level=business_card
```

### 🚀 Deployment

### Local Development

```bash
# Using virtual environment (recommended)
source venv/bin/activate

# Quick development start (recommended)
./scripts/dev-start.sh
# API: http://localhost:8004
# Frontend: http://localhost:8005

# Legacy single server method
python dev.py  # Runs on port 8004
```

### Docker Deployment

Docker provides **flexible deployment options** - deploy only what you need:

#### API Only (Headless Deployment)
Perfect for API integrations, mobile apps, or custom frontends:
```bash
# Just the API server
docker-compose up daemon-api

# Access API at http://localhost:8004
# Use cases: Mobile apps, API integrations, external frontends
```

#### Development Deployment
Complete setup for development:
```bash
# API + Frontend (development servers)
docker-compose --profile frontend-dev up

# Access Frontend at http://localhost:8005 (Python server)
# Access API at http://localhost:8004
```

#### Production Deployment
Enterprise-ready with nginx, SSL, and security:
```bash
# Setup SSL certificates first
./scripts/setup-ssl.sh

# Production stack with nginx + SSL
docker-compose -f docker-compose.prod.yml up -d

# Access via HTTPS at https://yourdomain.com
# Automatic HTTP to HTTPS redirect
```

#### API Only (Headless)
Perfect for API integrations, mobile apps, or custom frontends:
```bash
# Just the API server
docker-compose up daemon-api

# Access API at http://localhost:8004
# Use cases: Mobile apps, API integrations, external frontends
```

#### Custom Configuration
```bash
# Create custom environment
cp .env.example .env
# Edit .env with your settings (ports, domains, etc.)

# Deploy with custom settings
docker-compose --env-file .env up
```

**Use Cases:**
- **API Only**: Perfect for developers who want to build their own frontend
- **Frontend Only**: Great for frontend development against external APIs
- **Full Stack**: Complete solution for traditional web applications
- **Production**: Enterprise-ready with nginx, SSL, and proper security

**Docker Environment Variables:**
```bash
# In .env for docker-compose
SECRET_KEY=your-secure-secret-key
PORT=8004
DATABASE_URL=sqlite:///./data/daemon.db
BACKUP_ENABLED=true
```

### Remote Server (Raspberry Pi/Linux)

```bash
# Automated setup script (creates venv automatically)
chmod +x setup-pi.sh
sudo ./setup-pi.sh
```

The remote setup script:
- ✅ **Creates isolated virtual environment** at `/opt/daemon-pmac/venv/`
- ✅ **Installs all dependencies** in the venv
- ✅ **Sets up systemd service** using the venv Python
- ✅ **Configures automatic backups** with venv Python
- ✅ **No global package pollution**

### CI/CD Pipeline

GitHub Actions automatically:
- ✅ **Tests** in isolated environments (no venv needed)
- ✅ **Builds** Docker images
- ✅ **Deploys** to staging/production using venv on remote servers

**Key Point**: Remote deployments use virtual environments automatically via the setup scripts!

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key settings:
- `SECRET_KEY`: JWT signing key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `DATABASE_URL`: SQLite database path
- `RATE_LIMIT_REQUESTS`: Requests per minute per IP
- `BACKUP_ENABLED`: Enable automatic backups

## API Endpoints

### 🔄 Adaptive Routing System

The API automatically adapts based on the number of users:

**Single User Mode (≤1 user):**
```bash
GET /api/v1/resume          # Simple, clean endpoints
GET /api/v1/ideas
GET /api/v1/skills
```

**Multi-User Mode (2+ users):**
```bash
GET /api/v1/resume/users/pmac    # User-specific endpoints
GET /api/v1/ideas/users/kime
GET /api/v1/skills/users/pmac
```

### 📊 Core Data Endpoints

#### Personal Information
- `GET /api/v1/resume` - Professional resume and work history
- `GET /api/v1/skills` - Technical and soft skills
- `GET /api/v1/books` - Favorite books and reading lists
- `GET /api/v1/hobbies` - Hobbies and interests

#### Ideas & Projects
- `GET /api/v1/ideas` - Ideas and thoughts
- `GET /api/v1/problems` - Problems seeking solutions
- `GET /api/v1/looking_for` - What you're actively seeking
- `GET /api/v1/projects` - Project portfolio and work examples

### 🔐 Privacy-Aware Endpoints

All data endpoints support privacy filtering via query parameters:

```bash
# Public access (automatic privacy filtering)
GET /api/v1/resume?privacy_level=public_full

# Business card mode (minimal info)
GET /api/v1/resume?privacy_level=business_card

# AI assistant access (full data, sanitized)
GET /api/v1/resume?privacy_level=ai_safe

# Professional level (work-appropriate)
GET /api/v1/resume?privacy_level=professional
```

### 👑 Management Endpoints

#### Data Management
- `POST /api/v1/{endpoint}` - Add/update data (authenticated)
- `DELETE /api/v1/{endpoint}/{id}` - Delete data (authenticated)
- `GET /api/v1/endpoints` - List all available endpoints

#### User Management (Admin Only)
- `POST /auth/register` - Register new user
- `GET /auth/users` - List all users
- `POST /api/v1/setup/user/{username}` - Complete user setup

#### Privacy Management
- `GET /api/v1/privacy/settings` - Get privacy settings
- `PUT /api/v1/privacy/settings` - Update privacy settings
- `POST /api/v1/privacy/preview` - Preview privacy filtering

#### Multi-User Data Access (Admin/User)
- `GET /api/v1/{endpoint}/users/{username}` - Access specific user's data
- `POST /api/v1/import/user/{username}` - Import user data
- `POST /api/v1/import/all` - Import all users' data

### 🏥 System Endpoints
- `GET /health` - System health check
- `GET /api/v1/system/info` - System information and mode detection

## Adding New Endpoints

### Via API
```bash
curl -X POST "http://localhost:8000/api/v1/endpoints" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "projects",
    "description": "Current projects",
    "schema": {
      "name": {"type": "string", "required": true},
      "description": {"type": "string"},
      "status": {"type": "string", "enum": ["active", "completed", "paused"]}
    }
  }'
```

### Via CLI
```bash
python -m app.cli endpoint create projects "Current projects" \
  --field name:string:required \
  --field description:string \
  --field status:enum:active,completed,paused
```

## Backup & Recovery

### Manual Backup
```bash
python -m app.cli backup create
```

### Restore from Backup
```bash
python -m app.cli backup restore backup_20231215_143022.db
```

### Resume Management (Optional)
```bash
# Check if resume file exists and is valid
make check-resume

# Import resume from JSON file (auto-detects data/resume_pmac.json)
make import-resume

# View current resume data
make show-resume
```

See [RESUME_MANAGEMENT.md](RESUME_MANAGEMENT.md) for detailed resume import instructions.

### Automatic Backups
Set `BACKUP_ENABLED=true` in `.env` for daily automatic backups.

## Security Features

- JWT token authentication
- Rate limiting (configurable per endpoint)
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Request logging
- IP-based access control

## Monitoring

- Health check endpoint: `/health`
- Metrics endpoint: `/metrics` (Prometheus format)
- Database connection monitoring
- Request/response time tracking

## Production Deployment

### Raspberry Pi Setup

1. Install Python 3.9+
2. Clone repository
3. Set up systemd service
4. Configure nginx reverse proxy
5. Set up SSL certificate

Example systemd service:
```ini
[Unit]
Description=Daemon API
After=network.target

[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/daemon-pmac
Environment=PATH=/home/pi/daemon-pmac/venv/bin
ExecStart=/home/pi/daemon-pmac/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🌍 Remote Server Management

### Managing Your German Server from USA

If your server is running in Germany and you're in the USA, here are several ways to manage users and data:

#### **1. Direct API Access**
```bash
# Set your server URL (use your actual domain/IP)
export DAEMON_URL="https://daemon.pmac.dev"  # or http://YOUR_SERVER_IP:8004

# Create users via API (requires admin token)
curl -X POST "$DAEMON_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pmac",
    "email": "phil@pmac.dev",
    "password": "secure_password"
  }'

# Login to get admin token
TOKEN=$(curl -X POST "$DAEMON_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=pmac&password=secure_password" | jq -r '.access_token')

# Create additional users
curl -X POST "$DAEMON_URL/api/v1/setup/user/kime" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kime",
    "email": "kime@example.com",
    "password": "secure_password"
  }'
```

#### **2. SSH + CLI Access**
```bash
# SSH into your German server
ssh user@your-german-server.com

# Use CLI commands on the server
python -m app.cli create-user pmac
python -m app.cli create-user kime --admin
python -m app.cli import-all-data --base-dir /data/private
```

#### **3. File Upload + Import**
```bash
# Upload data files to server
scp -r ./data/private/* user@your-german-server.com:/app/data/private/

# Import via API
curl -X POST "$DAEMON_URL/api/v1/import/all" \
  -H "Authorization: Bearer $TOKEN"
```

#### **4. Docker Volume Management**
```bash
# If using Docker, copy data to container
docker cp ./data/private/pmac/ daemon-container:/app/data/private/pmac/

# Import data
docker exec daemon-container python -m app.cli import-user-data pmac
```

#### **5. Automated Setup Script**
Create a setup script for remote management:

```bash
#!/bin/bash
# setup-remote-users.sh

DAEMON_URL="https://daemon.pmac.dev"
ADMIN_USER="pmac"
ADMIN_PASS="your_secure_password"

# Login and get token
TOKEN=$(curl -s -X POST "$DAEMON_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER&password=$ADMIN_PASS" | jq -r '.access_token')

# Create users
for user in kime brianc; do
  echo "Creating user: $user"
  curl -X POST "$DAEMON_URL/api/v1/setup/user/$user" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"username\": \"$user\",
      \"email\": \"$user@example.com\",
      \"password\": \"temp_password_$user\"
    }"
done

echo "Users created successfully!"
```

### **Time Zone Considerations**
Since your server is in Germany (CET/CEST), keep in mind:
- **API timestamps** will be in UTC by default
- **Log files** will show German server time
- **Backup schedules** run on German server time
- **Rate limiting** resets on server time

### **Security Best Practices for Remote Management**
1. **Use HTTPS**: Always use `https://` for API calls
2. **Rotate tokens**: JWT tokens expire, get new ones as needed
3. **Use SSH keys**: For CLI access, use SSH key authentication
4. **VPN access**: Consider VPN for sensitive operations
5. **Audit logs**: Monitor who's accessing your server

## 📊 Data Management

### **Bulk Data Import**
```bash
# Import all users' data from directory structure
POST /api/v1/import/all?base_directory=data/private

# Import specific user's data
POST /api/v1/import/user/pmac?data_directory=data/private/pmac

# Import single file
POST /api/v1/import/file?file_path=data/private/pmac/resume.json&endpoint_name=resume
```

### **CLI Data Management**
```bash
# Create user with automatic data import
python -m app.cli create-user pmac --import-data

# Import data for existing users
python -m app.cli import-user-data pmac --data-dir data/private/pmac
python -m app.cli import-all-data --base-dir data/private

# Export user data (backup)
python -m app.cli export-user-data pmac --output-dir ./backups/
```

### **Expected Directory Structure**
```
data/
├── examples/              # Template files (tracked in git)
│   ├── resume_example.json
│   ├── skills_example.json
│   └── hobbies_example.json
└── private/              # User data (ignored by git)
    ├── pmac/
    │   ├── resume_pmac.json
    │   ├── skills_pmac.json
    │   └── hobbies_pmac.json
    ├── kime/
    │   ├── resume_kime.json
    │   └── skills_kime.json
    └── brianc/
        └── resume_brianc.json
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📖 Additional Documentation

For comprehensive development and deployment documentation, see the [`docs/`](docs/) directory:

- **[Development Setup](docs/VSCODE_SETUP.md)** - VS Code configuration and development environment
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Detailed architecture and file organization
- **[Data Management](docs/DATA_MANAGEMENT.md)** - Multi-user data import/export and privacy controls
- **[Server Setup](docs/SERVER_SETUP.md)** - Server configuration and deployment strategies
- **[Multi-App Hosting](docs/MULTI_APP_HOSTING.md)** - Multi-application hosting with nginx and Docker
- **[Remote Deployment](docs/REMOTE_MANAGEMENT.md)** - Server deployment and management
- **[Testing Guides](docs/)** - Unit and E2E testing strategies
- **[API Development](docs/ENDPOINT_ALIGNMENT.md)** - Endpoint tracking and alignment

## Attribution & Inspiration

This project is an **example implementation** of the concepts from:

**[Daemon - An open-source personal API framework](https://github.com/danielmiessler/Daemon)** by [Daniel Miessler](https://danielmiessler.com)

The original Daemon project outlines a vision for personal APIs that allow entities (people, companies, objects) to expose information about themselves through standardized endpoints. This implementation takes those concepts and provides:

- A complete, production-ready FastAPI implementation
- Enhanced security features (JWT auth, rate limiting, input validation)
- Database persistence with automatic backups
- Comprehensive CLI management tools
- Docker and Raspberry Pi deployment options
- Model Context Protocol (MCP) support for AI integration
- Extensive testing and monitoring capabilities

### Key Differences from Original Concept

While maintaining the core philosophy and endpoint structure of the original Daemon project, this implementation adds:

- **Database persistence**: SQLite backend with structured data storage
- **Authentication system**: JWT tokens and API keys for security
- **Admin interface**: User management and system administration
- **Deployment automation**: Scripts for Raspberry Pi and Docker deployment
- **Monitoring**: Health checks, metrics, and audit logging
- **Data management**: Import/export, backup/restore functionality

### Related Projects

Daniel Miessler has created an ecosystem of related projects:
- [Substrate](https://github.com/danielmiessler/substrate) - Framework for human understanding and progress
- [Fabric](https://github.com/danielmiessler/fabric) - AI-augmented productivity framework
- [TELOS](https://danielmiessler.com/telos) - Life optimization framework

## License

MIT License - see LICENSE file for details.

This project is independently developed and is not officially affiliated with Daniel Miessler or the original Daemon project, though it implements the same core concepts with gratitude and respect for the original vision.

### 🔐 Authentication & Authorization

#### Getting Started
```bash
# 1. Login to get JWT token (use your actual port)
curl -X POST "http://localhost:8004/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=pmac&password=your_password"

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "username": "pmac",
    "is_admin": true
  }
}
```

#### Using Authentication
```bash
# 2. Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8004/api/v1/resume"

# 3. Update data (authenticated endpoints)
curl -X POST "http://localhost:8004/api/v1/ideas" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "New Idea", "description": "A great concept"}'
```

#### 📝 Content Management Guide

For detailed instructions on creating, updating, and managing content, see the [Content Management Guide](docs/CONTENT_MANAGEMENT.md).

**Quick Content Management Workflow:**
1. **Login**: `POST /auth/login` → Get JWT token
2. **List Content**: `GET /api/v1/{endpoint}` (authenticated) → Get item IDs
3. **Update Content**: `PUT /api/v1/{endpoint}/{item_id}` → Modify specific content
4. **Public View**: `GET /api/v1/{endpoint}/users/{username}` → Clean display

**Two Endpoint Types:**
- **Authenticated**: Show content with item IDs for management
- **Public**: Show clean content without IDs for consumption

#### User Roles & Permissions

**Admin Users:**
- Create/manage other users
- Access all users' data
- System administration
- Import/export data for any user

**Regular Users:**
- Access only their own data
- Update their privacy settings
- Cannot create other users

#### Public vs Authenticated Access

**Public Endpoints (No Authentication):**
- `GET /api/v1/{endpoint}` - Privacy-filtered data
- `GET /health` - System health
- `GET /api/v1/system/info` - Basic system info

**Authenticated Endpoints (Token Required):**
- `POST /api/v1/{endpoint}` - Create/update data
- `DELETE /api/v1/{endpoint}/{id}` - Delete data
- `GET /api/v1/privacy/settings` - Privacy management
- `POST /api/v1/import/*` - Data import

## 📚 Interactive API Documentation

FastAPI automatically generates interactive API documentation:

### Swagger UI (Recommended)
```
http://localhost:8004/docs
```
- **Interactive**: Test endpoints directly in browser
- **Authentication**: Built-in JWT token support
- **Real-time**: Always up-to-date with current API
- **Multi-user aware**: Shows adaptive routing examples

### ReDoc (Alternative)
```
http://localhost:8004/redoc
```
- **Clean design**: Focused on readability
- **Comprehensive**: Detailed schema documentation
- **Export friendly**: Easy to print or share

### OpenAPI Schema
```
http://localhost:8004/openapi.json
```
- **Raw schema**: For automated tooling
- **Client generation**: Use with OpenAPI generators
- **Integration**: Perfect for external tools

### Usage Tips

1. **Authentication in Swagger**:
   - Click "Authorize" button
   - Enter `Bearer YOUR_JWT_TOKEN`
   - All subsequent requests will be authenticated

2. **Privacy Testing**:
   - Try different `privacy_level` parameters
   - Compare filtered vs unfiltered responses
   - Test with different user tokens

3. **Multi-User Testing**:
   - Create multiple users via `/auth/register`
   - Test user-specific endpoints
   - Verify data isolation between users
