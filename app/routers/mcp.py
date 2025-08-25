"""
MCP (Model Context Protocol) support for Daemon API
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import DataEntry, Endpoint, get_db
from ..schemas import MCPToolCallRequest, MCPToolCallResponse, MCPToolResponse

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol"])


def get_mcp_tools(db: Session) -> List[Dict[str, Any]]:
    """Generate MCP tool definitions from available endpoints"""
    tools = []

    # Get all active public endpoints
    endpoints = (
        db.query(Endpoint)
        .filter(Endpoint.is_active == True, Endpoint.is_public == True)
        .all()
    )

    for endpoint in endpoints:
        tool_name = f"{settings.mcp_tools_prefix}{endpoint.name}"

        # Create tool definition
        tool = {
            "name": tool_name,
            "description": f"Get {endpoint.description or endpoint.name} data",
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of items to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Return only active items",
                        "default": True,
                    },
                },
                "additionalProperties": False,
            },
        }

        tools.append(tool)

    # Add a general info tool
    tools.append(
        {
            "name": f"{settings.mcp_tools_prefix}info",
            "description": "Get information about available daemon endpoints",
            "input_schema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        }
    )

    return tools


@router.post("/tools/list")
async def list_mcp_tools(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """List available MCP tools"""
    if not settings.mcp_enabled:
        raise HTTPException(status_code=404, detail="MCP support is disabled")

    tools = get_mcp_tools(db)

    return {"jsonrpc": "2.0", "result": {"tools": tools}}


@router.post("/tools/call")
async def call_mcp_tool(
    request: MCPToolCallRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Execute an MCP tool call"""
    if not settings.mcp_enabled:
        raise HTTPException(status_code=404, detail="MCP support is disabled")

    tool_name = request.name
    arguments = request.arguments

    # Remove prefix to get endpoint name
    if not tool_name.startswith(settings.mcp_tools_prefix):
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": f"Invalid tool name: {tool_name}"},
        }

    endpoint_name = tool_name[len(settings.mcp_tools_prefix) :]

    try:
        if endpoint_name == "info":
            # Return information about available endpoints
            endpoints = (
                db.query(Endpoint)
                .filter(Endpoint.is_active == True, Endpoint.is_public == True)
                .all()
            )

            info = {
                "daemon_version": "0.1.0",
                "available_endpoints": [
                    {
                        "name": ep.name,
                        "description": ep.description,
                        "created_at": ep.created_at.isoformat(),
                    }
                    for ep in endpoints
                ],
                "total_endpoints": len(endpoints),
            }

            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": json.dumps(info, indent=2)}],
                    "is_error": False,
                },
            }

        else:
            # Get data from specific endpoint
            endpoint = (
                db.query(Endpoint)
                .filter(
                    Endpoint.name == endpoint_name,
                    Endpoint.is_active == True,
                    Endpoint.is_public == True,
                )
                .first()
            )

            if not endpoint:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": f"Endpoint '{endpoint_name}' not found or not public",
                    },
                }

            # Get parameters
            limit = min(arguments.get("limit", 10), 100)
            active_only = arguments.get("active_only", True)

            # Query data
            query = db.query(DataEntry).filter(DataEntry.endpoint_id == endpoint.id)
            if active_only:
                query = query.filter(DataEntry.is_active == True)

            data_entries = query.limit(limit).all()

            # Format response
            data = [entry.data for entry in data_entries]

            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "endpoint": endpoint_name,
                                    "description": endpoint.description,
                                    "count": len(data),
                                    "data": data,
                                },
                                indent=2,
                                default=str,
                            ),
                        }
                    ],
                    "is_error": False,
                },
            }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
        }


# Alternative REST-like endpoints for MCP compatibility
@router.get("/tools")
async def get_tools_rest(db: Session = Depends(get_db)):
    """REST endpoint to get available tools"""
    if not settings.mcp_enabled:
        raise HTTPException(status_code=404, detail="MCP support is disabled")

    tools = get_mcp_tools(db)
    return {"tools": tools}


@router.post("/tools/{tool_name}")
async def call_tool_rest(
    tool_name: str, arguments: Dict[str, Any], db: Session = Depends(get_db)
):
    """REST endpoint to call a specific tool"""
    if not settings.mcp_enabled:
        raise HTTPException(status_code=404, detail="MCP support is disabled")

    request = MCPToolCallRequest(name=tool_name, arguments=arguments)
    response = await call_mcp_tool(request, db)

    # Extract the result for REST format
    if "result" in response:
        return response["result"]
    elif "error" in response:
        raise HTTPException(status_code=400, detail=response["error"]["message"])
    else:
        raise HTTPException(status_code=500, detail="Unknown error")
