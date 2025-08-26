# Daemon-pmac: Detailed Requirements Specification

## 1. Executive Summary

Daemon-pmac is an **adaptive personal API framework** that seamlessly scales from single-user simplicity to multi-user complexity with comprehensive privacy controls. The system automatically adapts its behavior based on the number of users, providing clean single-user endpoints when appropriate and user-specific multi-user endpoints when needed.

**Core Philosophy**: Start simple for personal use, scale automatically to support teams and organizations.

---

## 2. System Architecture Overview

### 2.1 Technology Stack
- **Backend Framework**: FastAPI (Python 3.9+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with OAuth2 Bearer
- **API Documentation**: OpenAPI/Swagger with auto-generation
- **Deployment**: Docker, Docker Compose, systemd service
- **Testing**: pytest with E2E and unit test separation
- **Code Quality**: Black, isort, flake8, mypy, bandit

### 2.2 Adaptive Architecture
The system employs an adaptive architecture that automatically switches behavior based on user count:

- **≤1 User**: Single-user mode with simplified endpoints
- **≥2 Users**: Multi-user mode with user-specific routing

This design ensures the API remains simple for personal use while scaling to support collaborative environments.

---

## 3. Single-User Requirements

### 3.1 Core Endpoints (Single-User Mode)
When the system contains one or fewer users, endpoints follow a simplified pattern:

#### 3.1.1 Data Access Endpoints
```
GET    /api/v1/{endpoint_name}           # Retrieve endpoint data
POST   /api/v1/{endpoint_name}           # Create new data entry
PUT    /api/v1/{endpoint_name}/{id}      # Update specific entry
DELETE /api/v1/{endpoint_name}/{id}      # Delete specific entry
```

#### 3.1.2 Default Endpoints
The system provides eight core endpoints based on Daniel Miessler's original Daemon concept:

| Endpoint | Description | Schema Elements |
|----------|-------------|-----------------|
| `resume` | Professional resume and work history | name, title, contact, experience, education, skills |
| `about` | Basic personal/entity information | name, bio, location, interests |
| `ideas` | Ideas, thoughts, and concepts | title, description, category, status, tags |
| `skills` | Technical and soft skills | name, level, category, years_experience |
| `favorite_books` | Book recommendations and reviews | title, author, isbn, rating, review, genres |
| `problems` | Problems being worked on or solved | title, description, status, priority |
| `hobbies` | Personal interests and hobbies | name, description, skill_level, time_invested |
| `looking_for` | Things currently being sought | category, description, priority, status |

#### 3.1.3 Single-User Authentication
- **First User Registration**: Automatically becomes admin
- **Simple Authentication**: Username/password with JWT tokens
- **Optional Operation**: Many endpoints can be accessed without authentication based on privacy settings

### 3.2 Single-User Privacy Controls
- **Public by Default**: Data is publicly accessible unless explicitly restricted
- **Privacy Levels**:
  - `business_card`: Minimal networking information
  - `professional`: Work-appropriate details only
  - `public_full`: Complete public view
  - `ai_safe`: Safe for AI assistant consumption

### 3.3 Single-User Data Management
- **File-based Import**: JSON files in `data/` directory
- **Automatic Discovery**: System discovers `{endpoint}.json` files
- **CLI Management**: Command-line tools for data import/export
- **Git-safe**: Comprehensive `.gitignore` protects personal data

---

## 4. Multi-User Requirements

### 4.1 Adaptive Routing (Multi-User Mode)
When two or more users exist, the system automatically switches to multi-user mode:

#### 4.1.1 User-Specific Endpoints
```
GET    /api/v1/{endpoint_name}/users/{username}      # User-specific data access
POST   /api/v1/{endpoint_name}/users/{username}      # Create data for user
PUT    /api/v1/{endpoint_name}/users/{username}/{id} # Update user's data
DELETE /api/v1/{endpoint_name}/users/{username}/{id} # Delete user's data
```

#### 4.1.2 Alternative Routing Pattern
```
GET    /api/v1/users/{username}/{endpoint_name}      # Alternative user-specific access
```

Both patterns are supported to accommodate different client preferences.

### 4.2 Multi-User Authentication & Authorization

#### 4.2.1 User Management
- **Admin Users**: Full system access, user management capabilities
- **Regular Users**: Access to own data and public data from others
- **User Status**: Active/inactive toggle by admins
- **Admin Promotion**: Admins can promote regular users to admin status

#### 4.2.2 Authentication Methods
- **JWT Tokens**: Primary authentication mechanism
- **API Keys**: For programmatic access and external integrations
- **Session Management**: Automatic token refresh and expiration handling

#### 4.2.3 Authorization Levels
- **Public Access**: No authentication required for public data
- **User Access**: JWT token required for personal data access
- **Admin Access**: Admin privileges required for system management

### 4.3 Multi-User Data Isolation

#### 4.3.1 User Data Separation
- **Database-Level Isolation**: `created_by_id` foreign key on all data entries
- **Directory Structure**: `data/private/{username}/` for user-specific files
- **Import Isolation**: Users can only import data to their own namespace

#### 4.3.2 Cross-User Data Access
- **Public Data**: Accessible to all users based on privacy settings
- **Private Data**: Only accessible to owner and admins
- **Privacy Filtering**: Automatic content filtering based on privacy levels

### 4.4 Multi-User Privacy System

#### 4.4.1 Per-User Privacy Settings
```json
{
  "default_privacy_level": "public_full",
  "endpoint_specific": {
    "resume": "professional",
    "ideas": "ai_safe",
    "favorite_books": "public_full"
  },
  "custom_filters": {
    "hide_contact_info": true,
    "hide_salary_info": true,
    "hide_personal_projects": false
  }
}
```

#### 4.4.2 Privacy Levels (Multi-User)
- **business_card**: Name, title, basic contact only
- **professional**: Work-related information, no personal details
- **public_full**: Complete information respecting user privacy settings
- **ai_safe**: Sanitized data safe for AI processing
- **none**: Full access (authenticated users only)

#### 4.4.3 Automatic Data Sanitization
- **Sensitive Data Detection**: Automatic removal of phone numbers, SSNs, addresses
- **Context-Aware Filtering**: Different filters for different privacy levels
- **User-Controlled**: Users can override automatic filtering

---

## 5. Administrative Requirements

### 5.1 User Management
```
GET    /admin/users                    # List all users
PUT    /admin/users/{id}/toggle        # Toggle user active status
PUT    /admin/users/{id}/admin         # Promote/demote admin status
```

### 5.2 System Management

#### 5.2.1 Endpoint Management
```
GET    /admin/endpoints               # List all endpoints
PUT    /admin/endpoints/{id}/toggle   # Toggle endpoint active status
DELETE /admin/endpoints/{id}          # Delete custom endpoint
```

#### 5.2.2 Data Management
```
GET    /admin/data/stats             # System data statistics
DELETE /admin/data/cleanup           # Clean up inactive/orphaned data
```

#### 5.2.3 Backup & Recovery
```
POST   /admin/backup                 # Create manual backup
GET    /admin/backups                # List available backups
POST   /admin/restore/{filename}     # Restore from backup
```

### 5.3 API Key Management
```
GET    /admin/api-keys               # List all API keys
POST   /admin/api-keys               # Create new API key
DELETE /admin/api-keys/{id}          # Revoke API key
```

### 5.4 Audit & Monitoring
```
GET    /admin/audit                  # View audit logs
GET    /admin/system                 # System health and metrics
```

---

## 6. Security Requirements

### 6.1 Authentication Security
- **Password Hashing**: bcrypt with configurable rounds
- **JWT Security**: Configurable secret key and expiration
- **API Key Security**: Secure random generation with expiration support
- **Session Management**: Automatic cleanup of expired tokens

### 6.2 Access Control
- **IP-based Restrictions**: Configurable allowed IP lists
- **Rate Limiting**: Configurable request rate limits per IP
- **CORS Configuration**: Flexible cross-origin request handling
- **Security Headers**: Automatic security header injection

### 6.3 Data Protection
- **Input Validation**: Comprehensive request validation with Pydantic
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Prevention**: Automatic output encoding and sanitization
- **Privacy Filtering**: Automatic PII detection and removal

### 6.4 Infrastructure Security
- **HTTPS Support**: SSL/TLS certificate integration
- **Docker Security**: Non-root container execution
- **File Permissions**: Proper file system permissions
- **Environment Variables**: Secure configuration management

---

## 7. Data Management Requirements

### 7.1 Data Import/Export

#### 7.1.1 Single-User Data Import
```bash
# Automatic discovery of data files
python -m app.cli data discover

# Import specific endpoint
python -m app.cli data import ideas --file data/ideas.json

# Import all discovered files
python -m app.cli data import-all
```

#### 7.1.2 Multi-User Data Import
```bash
# Import data for specific user
python -m app.cli data import ideas --user pmac --file data/private/pmac/ideas.json

# Setup new user with data directory
python -m app.cli user setup pmac --create-dirs --import-data
```

#### 7.1.3 File Pattern Support
- `{endpoint}.json` - Simple format
- `{endpoint}_{suffix}.json` - With descriptive suffix
- `{endpoint}_{username}.json` - User-specific files
- Discovery from `data/` and `data/private/{username}/` directories

### 7.2 Database Management

#### 7.2.1 Automatic Backups
- **Scheduled Backups**: Configurable backup intervals
- **Retention Policy**: Automatic cleanup of old backups
- **Backup Validation**: Integrity checking of backup files
- **Disaster Recovery**: Point-in-time recovery capabilities

#### 7.2.2 Database Schema Management
- **Automatic Migrations**: Schema updates handled automatically
- **Data Validation**: Comprehensive validation before storage
- **Referential Integrity**: Foreign key constraints and cascading
- **Performance Optimization**: Automatic indexing for common queries

---

## 8. API Integration Requirements

### 8.1 Model Context Protocol (MCP) Support
```
POST   /mcp/tools/list               # List available MCP tools
POST   /mcp/tools/call               # Execute MCP tool
GET    /mcp/tools                    # Get tool definitions
POST   /mcp/tools/{tool_name}        # Execute specific tool
```

#### 8.1.1 MCP Tool Generation
- **Automatic Tool Creation**: Generate MCP tools from active endpoints
- **Schema Integration**: Use endpoint schemas for tool parameters
- **Privacy-Aware**: Respect privacy settings in tool responses
- **Configurable Prefix**: Customizable tool naming conventions

### 8.2 REST API Standards
- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Responses**: Consistent JSON response format
- **Error Handling**: Standardized error response structure
- **Pagination**: Configurable pagination for large datasets

### 8.3 OpenAPI Documentation
- **Auto-Generation**: Automatic OpenAPI schema generation
- **Interactive Docs**: Swagger UI and ReDoc interfaces
- **Dynamic Examples**: Context-aware example generation
- **Schema Validation**: Real-time request/response validation

---

## 9. Privacy & Compliance Requirements

### 9.1 Privacy by Design
- **Default Privacy**: Secure defaults for all privacy settings
- **User Control**: Granular privacy control for each user
- **Data Minimization**: Only collect and store necessary data
- **Purpose Limitation**: Data used only for stated purposes

### 9.2 Data Subject Rights
- **Data Access**: Users can access all their stored data
- **Data Portability**: Export functionality for user data
- **Data Correction**: Users can update/correct their information
- **Data Deletion**: Complete removal of user data on request

### 9.3 Audit & Compliance
- **Audit Logging**: Comprehensive logging of all data access and modifications
- **Privacy Impact**: Automatic assessment of privacy implications
- **Compliance Reporting**: Generate compliance reports for regulations
- **Data Retention**: Configurable data retention policies

---

## 10. Performance & Scalability Requirements

### 10.1 Performance Targets
- **Response Time**: < 200ms for simple GET requests
- **Throughput**: Support 1000+ requests per minute
- **Database Performance**: Optimized queries with proper indexing
- **Memory Usage**: Efficient memory management for long-running processes

### 10.2 Scalability Architecture
- **Horizontal Scaling**: Support for multiple application instances
- **Database Scaling**: Connection pooling and query optimization
- **Caching Strategy**: Response caching for frequently accessed data
- **Load Balancing**: Support for load balancer integration

### 10.3 Resource Management
- **Connection Limits**: Configurable database connection limits
- **Rate Limiting**: Prevent resource exhaustion from excessive requests
- **Monitoring**: Health checks and performance metrics
- **Graceful Degradation**: Maintain functionality under load

---

## 11. Deployment & Operations Requirements

### 11.1 Deployment Options
- **Standalone Python**: Direct Python execution for development
- **Docker Container**: Containerized deployment for production
- **Docker Compose**: Multi-container orchestration
- **Systemd Service**: System service integration for Linux

### 11.2 Configuration Management
- **Environment Variables**: Secure configuration via environment
- **Configuration Files**: Support for `.env` file configuration
- **Runtime Configuration**: Some settings configurable at runtime
- **Validation**: Configuration validation on startup

### 11.3 Monitoring & Logging
- **Health Endpoints**: `/health` endpoint for system monitoring
- **Structured Logging**: JSON-formatted logs for analysis
- **Metrics Collection**: Performance and usage metrics
- **Error Tracking**: Comprehensive error logging and reporting

### 11.4 Backup & Recovery
- **Automated Backups**: Scheduled database backups
- **Backup Verification**: Automatic backup integrity checking
- **Point-in-Time Recovery**: Restore to specific points in time
- **Disaster Recovery**: Complete system recovery procedures

---

## 12. Development & Testing Requirements

### 12.1 Code Quality Standards
- **Type Checking**: Full mypy type checking
- **Code Formatting**: Black code formatting
- **Import Sorting**: isort import organization
- **Linting**: flake8 style checking
- **Security Scanning**: bandit security analysis

### 12.2 Testing Strategy
- **Unit Tests**: Comprehensive unit test coverage
- **Integration Tests**: API endpoint integration testing
- **E2E Tests**: Full system end-to-end testing
- **Performance Tests**: Load and performance testing
- **Security Tests**: Security vulnerability testing

### 12.3 CI/CD Pipeline
- **Automated Testing**: Full test suite on every commit
- **Code Quality Gates**: Quality checks prevent bad commits
- **Security Scanning**: Automated security vulnerability scanning
- **Dependency Updates**: Automated dependency updates
- **Multi-Platform Testing**: Testing across Python versions and platforms

---

## 13. Future Enhancement Requirements

### 13.1 Advanced Features (Roadmap)
- **Real-time Notifications**: WebSocket support for live updates
- **Plugin System**: Extensible plugin architecture
- **Advanced Analytics**: Data insights and analytics dashboard
- **Mobile API**: Optimized endpoints for mobile applications
- **GraphQL Support**: Alternative query interface

### 13.2 Enterprise Features
- **SSO Integration**: SAML/OIDC single sign-on support
- **Advanced RBAC**: Role-based access control system
- **Multi-tenancy**: Support for multiple isolated tenants
- **Advanced Auditing**: Detailed audit trails and compliance reporting
- **High Availability**: Clustering and failover support

### 13.3 Integration Capabilities
- **Webhook Support**: Outbound notifications for data changes
- **External APIs**: Integration with external data sources
- **Calendar Integration**: Personal calendar data synchronization
- **Social Media**: Optional social media profile integration
- **Cloud Storage**: Integration with cloud storage providers

---

## 14. Conclusion

Daemon-pmac represents a comprehensive personal API framework that adapts to user needs while maintaining simplicity and security. The adaptive architecture ensures that single users enjoy a clean, simple experience while multi-user environments receive the full power of user isolation, privacy controls, and administrative capabilities.

The system's focus on privacy by design, comprehensive security, and automatic scaling makes it suitable for personal use cases ranging from individual developers to small teams and organizations requiring secure personal data management.

**Key Differentiators:**
1. **Adaptive Architecture**: Seamless single-user to multi-user transition
2. **Privacy by Design**: Comprehensive privacy controls and data protection
3. **Developer Experience**: Excellent tooling, documentation, and testing
4. **Production Ready**: Full deployment, monitoring, and operational capabilities
5. **Standards Compliant**: RESTful APIs, OpenAPI documentation, MCP integration

This requirements specification serves as the definitive guide for understanding, implementing, and extending the Daemon-pmac system.
