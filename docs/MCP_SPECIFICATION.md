# Model Context Protocol (MCP) Specification

## Overview

The Daemon API implements Model Context Protocol (MCP) support to provide AI assistants with structured, privacy-aware access to personal data endpoints. This implementation follows the MCP standard while adding privacy filtering and user consent mechanisms.

## Core Components

### 1. MCP Router (`app/routers/mcp.py`)
- **Purpose**: Handles MCP protocol endpoints and tool execution
- **Prefix**: `/mcp`
- **Features**: JSON-RPC compliance, privacy filtering, dynamic tool generation

### 2. Tool Generation System
- **Auto-discovery**: Automatically generates MCP tools from active database endpoints
- **Schema Integration**: Uses endpoint schemas for tool parameter validation
- **Privacy-Aware**: Applies user privacy settings to tool responses

## API Endpoints

### 2.1 Tool Discovery

#### `POST /mcp/tools/list`
List all available MCP tools with their schemas.

**Request Format (JSON-RPC):**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": "unique-request-id"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "tools": [
      {
        "name": "daemon_resume",
        "description": "Get resume data",
        "input_schema": {
          "type": "object",
          "properties": {
            "limit": {
              "type": "integer",
              "description": "Maximum number of items to return",
              "default": 10,
              "minimum": 1,
              "maximum": 100
            },
            "active_only": {
              "type": "boolean",
              "description": "Return only active items",
              "default": true
            }
          },
          "additionalProperties": false
        }
      }
    ]
  }
}
```

#### `GET /mcp/tools` (REST Alternative)
Get tool definitions via REST endpoint.

### 2.2 Tool Execution

#### `POST /mcp/tools/call`
Execute an MCP tool with specified arguments.

**Request:**
```json
{
  "name": "daemon_resume",
  "arguments": {
    "limit": 5,
    "active_only": true
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"endpoint\": \"resume\", \"description\": \"Resume information\", \"count\": 1, \"data\": [...filtered_data...]}"
      }
    ],
    "is_error": false
  }
}
```

#### `POST /mcp/tools/{tool_name}` (REST Alternative)
Execute specific tool via REST endpoint.

## Tool Naming Convention

### Standard Prefix
All MCP tools use the configurable prefix (default: `daemon_`):
- `daemon_resume` - Resume data access
- `daemon_about` - About/bio information
- `daemon_ideas` - Ideas and projects
- `daemon_skills` - Skills and competencies
- `daemon_contact_info` - Contact information
- `daemon_info` - System information and available endpoints

### Special Tools

#### `daemon_info`
Provides metadata about the Daemon API:
- Available endpoints
- System version
- Endpoint descriptions
- Creation timestamps

## Privacy and Security

### 3.1 Privacy Filtering
All MCP tool responses undergo automatic privacy filtering:

#### AI-Safe Filtering
- Removes sensitive patterns (SSN, phone numbers, addresses)
- Filters out personal financial information
- Sanitizes medical/health data
- Preserves professional and educational information

#### Visibility Levels
Data entries respect `meta.visibility` settings:
- `public` - Available to MCP tools (with AI-safe filtering)
- `private` - Excluded from MCP responses
- `unlisted` - Excluded from MCP responses

### 3.2 User Privacy Settings
Individual privacy controls override default filtering:
- `show_contact_info` - Controls contact data exposure
- `show_location` - Controls location/address data
- `show_current_company` - Controls current employment info
- `show_salary_range` - Controls compensation data
- `business_card_mode` - Ultra-minimal public view
- `ai_assistant_access` - Global MCP access toggle

### 3.3 Security Features
- **Authentication**: No authentication required for MCP endpoints (public read-only)
- **Rate Limiting**: Configurable request limits
- **Data Sanitization**: Automatic removal of sensitive patterns
- **Error Handling**: Safe error responses without data leakage

## Configuration

### 4.1 Environment Variables
```env
MCP_ENABLED=true                    # Enable/disable MCP support
MCP_TOOLS_PREFIX=daemon_           # Tool name prefix
```

### 4.2 Settings Integration
```python
from app.config import settings

# Check if MCP is enabled
if settings.mcp_enabled:
    # MCP functionality available
```

## Tool Schema Structure

### 5.1 Base Tool Definition
```json
{
  "name": "daemon_{endpoint_name}",
  "description": "Get {endpoint_description} data",
  "input_schema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer",
        "description": "Maximum number of items to return",
        "default": 10,
        "minimum": 1,
        "maximum": 100
      },
      "active_only": {
        "type": "boolean",
        "description": "Return only active items",
        "default": true
      }
    },
    "additionalProperties": false
  }
}
```

### 5.2 Info Tool Schema
```json
{
  "name": "daemon_info",
  "description": "Get information about available daemon endpoints",
  "input_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

## Data Flow

### 6.1 Tool Generation Process
1. Query active, public endpoints from database
2. Generate tool definitions with schemas
3. Add special `daemon_info` tool
4. Return tool list to client

### 6.2 Tool Execution Process
1. Validate tool name and prefix
2. Extract endpoint name from tool name
3. Query database for matching endpoint
4. Fetch data entries with pagination
5. Apply privacy filtering (AI-safe level)
6. Return filtered, serialized data

## Error Handling

### 7.1 Error Response Format
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Error description"
  }
}
```

### 7.2 Common Error Codes
- `-32603` - Internal error
- `-32602` - Invalid params
- `-32601` - Method not found
- `-32600` - Invalid request

### 7.3 HTTP Status Codes
- `200` - Success (including JSON-RPC errors)
- `404` - MCP disabled or tool not found
- `422` - Invalid request format

## Testing

### 8.1 Unit Tests (`tests/unit/test_mcp.py`)
- Tool generation logic
- Schema validation
- Error handling
- Privacy filtering

### 8.2 E2E Tests (`tests/e2e/test_mcp.py`)
- Full request/response cycle
- Privacy filtering integration
- Authentication scenarios
- Data visibility controls

### 8.3 Test Coverage Areas
- Tool discovery endpoints
- Tool execution with various parameters
- Privacy filtering scenarios
- Error conditions
- JSON-RPC compliance

## Integration Examples

### 8.1 Claude/ChatGPT Integration
```python
# Configure MCP client
mcp_client = MCPClient("http://localhost:8007/mcp")

# Discover available tools
tools = await mcp_client.list_tools()

# Execute tool
result = await mcp_client.call_tool("daemon_resume", {"limit": 1})
```

### 8.2 Manual Testing
```bash
# List available tools
curl -X POST http://localhost:8007/mcp/tools/list \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": "1"}'

# Execute tool
curl -X POST http://localhost:8007/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "daemon_ideas", "arguments": {"limit": 5}}'

# REST-style execution
curl -X POST http://localhost:8007/mcp/tools/daemon_skills \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "active_only": true}'
```

## Implementation Notes

### 9.1 Dependencies
- FastAPI for HTTP handling
- SQLAlchemy for database operations
- Pydantic for schema validation
- JSON standard library for serialization

### 9.2 Performance Considerations
- Database query optimization with indexes
- Configurable result limits (max 100 items)
- Efficient privacy filtering algorithms
- Minimal memory footprint for large datasets

### 9.3 Future Enhancements
- Streaming responses for large datasets
- Advanced filtering capabilities
- Custom tool parameter schemas
- Webhook notifications for data changes
- Real-time tool updates

## Compliance

This implementation follows the Model Context Protocol specification while adding:
- Enhanced privacy controls
- User consent mechanisms
- Safe AI data exposure
- Comprehensive error handling
- Production-ready security features

The MCP implementation enables secure, privacy-aware AI assistant integration with personal data while maintaining full user control over data exposure and access patterns.
