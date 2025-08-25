# Daemon-pmac Project Structure

**Example Implementation of [Daniel Miessler's Daemon Project](https://github.com/danielmiessler/Daemon)**

> This is a production-ready implementation of the personal API framework concept outlined in the original Daemon project by Daniel Miessler.

```
Daemon-pmac/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application and startup
│   ├── config.py                # Configuration management
│   ├── database.py              # Database models and setup
│   ├── schemas.py               # Pydantic models for validation
│   ├── auth.py                  # Authentication and security
│   ├── utils.py                 # Utility functions
│   ├── cli.py                   # Command-line interface
│   └── routers/                 # API route modules
│       ├── __init__.py
│       ├── auth.py              # Authentication routes
│       ├── api.py               # Core API endpoints
│       ├── admin.py             # Admin management routes
│       └── mcp.py               # Model Context Protocol routes
├── tests/                       # Test suite
│   ├── conftest.py             # Test configuration and fixtures
│   ├── test_auth.py            # Authentication tests
│   ├── test_api.py             # API endpoint tests
│   ├── test_mcp.py             # MCP functionality tests
│   └── test_utils.py           # Utility function tests
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata and tool config
├── Dockerfile                  # Docker container configuration
├── docker-compose.yml         # Multi-container setup
├── nginx.conf                  # Nginx reverse proxy config
├── daemon-pmac.service        # Systemd service file
├── setup-pi.sh               # Raspberry Pi installation script
├── setup-ssl.sh              # SSL certificate setup script
├── dev.py                     # Development server script
├── Makefile                   # Development commands
├── .env.example              # Environment configuration template
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT license
├── README.md                # Project documentation
└── data/                    # Data files and examples
    ├── README.md                           # Data directory overview
    ├── examples/                           # Example data files (tracked in git)
    │   ├── resume/                         # Resume endpoint examples and docs
    │   │   ├── resume_example.json
    │   │   ├── README.md
    │   │   ├── RESUME_MANAGEMENT.md
    │   │   └── RESUME_IMPORT_SUMMARY.md
    │   ├── skills/                         # Skills endpoint examples and docs
    │   │   ├── skills_example.json
    │   │   └── README.md
    │   ├── books/                          # Books endpoint examples and docs
    │   │   ├── favorite_books_example.json
    │   │   └── README.md
    │   ├── hobbies/                        # Hobbies endpoint examples and docs
    │   ├── ideas/                          # Ideas endpoint examples and docs
    │   ├── problems/                       # Problems endpoint examples and docs
    │   └── looking_for/                    # Looking for endpoint examples and docs
    └── private/                            # User data (ignored by git)
        └── {username}/                     # Per-user directories
            ├── resume/                     # User's resume data
            ├── skills/                     # User's skills data
            ├── books/                      # User's favorite books
            ├── hobbies/                    # User's hobbies
            ├── ideas/                      # User's ideas
            ├── problems/                   # User's problems
            └── looking_for/                # What user is looking for
```

## Key Features Implemented

### 🏗️ Architecture
- **FastAPI-based**: High-performance async API with automatic OpenAPI docs
- **SQLite database**: Lightweight with automatic migrations and backups
- **Modular design**: Clean separation of concerns with routers and middleware
- **Pydantic validation**: Strong type checking and data validation

### 🔐 Security
- **JWT authentication**: Secure token-based authentication
- **API key support**: Alternative authentication method
- **Rate limiting**: Configurable request throttling
- **Input sanitization**: XSS and injection prevention
- **CORS configuration**: Cross-origin request handling
- **IP filtering**: Optional IP-based access control
- **Security headers**: OWASP recommended HTTP headers

### 📊 Core Endpoints (Based on Original Daemon Project)
- `/api/v1/resume` - Professional resume and work history
- `/api/v1/about` - Personal/entity information
- `/api/v1/ideas` - Ideas and thoughts
- `/api/v1/skills` - Skills and expertise
- `/api/v1/favorite_books` - Book recommendations
- `/api/v1/problems` - Problems being solved
- `/api/v1/hobbies` - Hobbies and interests
- `/api/v1/looking_for` - Things currently seeking

### 🔌 Extensibility
- **Dynamic endpoints**: Create new endpoints via API or CLI
- **Custom schemas**: Define validation rules for each endpoint
- **Bulk operations**: Import/export data in JSON or CSV
- **MCP support**: Model Context Protocol for AI integration

### 🛠️ Management & Operations
- **CLI interface**: Complete command-line management
- **Health monitoring**: Built-in health checks and metrics
- **Automatic backups**: Scheduled database backups
- **Audit logging**: Track all data changes
- **Admin interface**: User and system management
- **Data export/import**: Flexible data portability

### 🐳 Deployment Options
- **Docker**: Containerized deployment with docker-compose
- **Raspberry Pi**: Optimized setup scripts for ARM devices
- **Systemd**: Native Linux service integration
- **Nginx**: Reverse proxy with SSL termination
- **Let's Encrypt**: Automatic SSL certificate management

### 🧪 Testing & Quality
- **Comprehensive tests**: Full test suite with pytest
- **Code formatting**: Black and isort integration
- **Type checking**: MyPy static analysis
- **Load testing**: Basic performance testing tools

### 📈 Monitoring & Observability
- **Prometheus metrics**: Built-in metrics endpoint
- **Structured logging**: JSON logging with levels
- **Performance tracking**: Request timing and resource usage
- **System monitoring**: CPU, memory, and disk usage

## Quick Start Commands

```bash
# Development
make install          # Install dependencies
make dev             # Start development server
make test            # Run tests
make format          # Format code

# Production (Raspberry Pi)
chmod +x setup-pi.sh
./setup-pi.sh        # Automated setup

# Docker
make docker-build    # Build container
make docker-run      # Start with compose

# Database
make db-init         # Initialize database
make backup          # Create backup
make create-user     # Add new user

# SSL Setup
./setup-ssl.sh --letsencrypt -d yourdomain.com -e your@email.com
```

## Configuration

All configuration is done via environment variables or the `.env` file:

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./daemon.db
RATE_LIMIT_REQUESTS=60
CORS_ORIGINS=["http://localhost:3000"]
BACKUP_ENABLED=true
MCP_ENABLED=true
```

## API Examples

```bash
# Get resume data
curl http://localhost:8000/api/v1/resume

# Get all ideas
curl http://localhost:8000/api/v1/ideas

# Add new resume entry (requires authentication)
curl -X POST http://localhost:8000/api/v1/resume \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "title": "Software Engineer",
    "summary": "Experienced developer with Python expertise",
    "contact": {
      "email": "john@example.com",
      "location": "San Francisco, CA"
    }
  }'

# Add new idea (requires authentication)
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "New Idea", "description": "A great idea"}'

# Create custom endpoint
curl -X POST http://localhost:8000/api/v1/endpoints \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "projects",
    "description": "Current projects",
    "schema": {
      "name": {"type": "string", "required": true},
      "status": {"type": "string", "enum": ["active", "completed"]}
    }
  }'
```

## MCP Integration

The framework includes Model Context Protocol support for AI integration:

```bash
# List available tools
curl -X POST http://localhost:8000/mcp/tools/list

# Call a tool
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "daemon_ideas", "arguments": {"limit": 5}}'
```

This framework provides everything needed to deploy a secure, scalable personal API on a Raspberry Pi or any Linux server, with comprehensive documentation, testing, and deployment automation.
