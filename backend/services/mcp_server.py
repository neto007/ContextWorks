"""
MCP (Model Context Protocol) Server
Implements MCP protocol over SSE (Server-Sent Events) with JSON-RPC 2.0.
"""
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from fastapi import Request, HTTPException
from sse_starlette.sse import EventSourceResponse

from services import tool_service, execution_service, mcp_manager

# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

class MCPServer:
    """MCP Protocol Server Implementation"""
    
    def __init__(self, mcp_id: str):
        self.mcp_id = mcp_id
        self.mcp_config = mcp_manager.get_mcp_server(mcp_id)
        if not self.mcp_config:
            raise ValueError(f"MCP server not found: {mcp_id}")
        
        self.protocol_version = "2024-11-05"
        self.tools_cache = None
    
    def _parse_yaml_metadata(self, yaml_path: str) -> Dict[str, Any]:
        """Parse script metadata from YAML file (inline from parser.py)."""
        import yaml
        import os
        meta = {"description": "",  "arguments": []}
        
        if not yaml_path or not os.path.exists(yaml_path):
            return meta
        
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f) or {}
            meta["description"] = data.get("description", "")
            
            # Parse arguments from schema
            schema = data.get("schema", {})
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for arg_name, arg_details in properties.items():
                meta["arguments"].append({
                    "name": arg_name,
                    "type": arg_details.get("type", "string"),
                    "description": arg_details.get("description", ""),
                    "default": arg_details.get("default"),
                    "required": arg_name in required
                })
        except Exception:
            pass
        
        return meta
        
    def get_tool_by_id(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get tool details by ID."""
        all_tools = tool_service.scan_tools()
        for category_tools in all_tools.values():
            for tool in category_tools:
                if tool['id'] == tool_id:
                    # Load full metadata (inline parser functionality)
                    meta = self._parse_yaml_metadata(tool['yaml_path'])
                    return {**tool, **meta}
        return None
    
    def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get tools registered with this MCP in MCP schema format."""
        if self.tools_cache:
            return self.tools_cache
        
        mcp_tools = []
        tool_ids = self.mcp_config.get('tool_ids', [])
        
        for tool_id in tool_ids:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                continue
            
            # Convert tool to MCP schema
            mcp_tool = self.tool_to_mcp_schema(tool)
            mcp_tools.append(mcp_tool)
        
        self.tools_cache = mcp_tools
        return mcp_tools
    
    def tool_to_mcp_schema(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert tool metadata to MCP tool schema.
        """
        # Convert arguments to JSON schema
        properties = {}
        required = []
        
        for arg in tool.get('arguments', []):
            arg_name = arg['name']
            arg_type = arg.get('type', 'str')
            
            # Map Python types to JSON schema types
            json_type = {
                'str': 'string',
                'int': 'integer',
                'float': 'number',
                'bool': 'boolean',
                'list': 'array',
                'dict': 'object'
            }.get(arg_type, 'string')
            
            properties[arg_name] = {
                'type': json_type,
                'description': arg.get('description', '')
            }
            
            # Add default if present
            if 'default' in arg and arg['default'] is not None:
                properties[arg_name]['default'] = arg['default']
            
            # Track required fields
            if arg.get('required', False):
                required.append(arg_name)
        
        # Build Env Vars Schema from MCP Config
        env_properties = {}
        env_required = []
        
        server_env_vars = self.mcp_config.get('env_vars', [])
        # Ensure it's a list (backward compat)
        if isinstance(server_env_vars, dict):
            server_env_vars = [] 
            
        for env_var in server_env_vars:
            name = env_var.get('name')
            if not name: continue
            
            # Check Scope
            scope = env_var.get('tool_ids', [])
            if scope and tool['id'] not in scope:
                continue

            
            env_properties[name] = {
                "type": "string",
                "description": env_var.get('description', '')
            }
            
            # Note: We do NOT expose the default value in the schema description to avoid leaking secrets
            # The client just needs to know it exists or is required
            
            if env_var.get('required', False):
                env_required.append(name)
        
        # Env schema object
        env_schema = {
            "type": "object",
            "properties": env_properties,
            "description": "Environment variables to inject into the tool execution context"
        }
        
        # Only set required if strictly needed by server configuration
        if env_required:
            env_schema["required"] = env_required
        else:
             # Allow any other env vars if not strict
             env_schema["additionalProperties"] = {"type": "string"}

        return {
            'name': tool['id'],
            'description': tool.get('description', ''),
            'inputSchema': {
                'type': 'object',
                'properties': {
                    **properties,
                    "env": env_schema
                },
                'required': required
            }
        }
    
    def create_jsonrpc_response(self, id: Any, result: Any = None, error: Dict = None) -> Dict:
        """Create JSON-RPC 2.0 response."""
        response = {
            'jsonrpc': '2.0',
            'id': id
        }
        
        if error:
            response['error'] = error
        else:
            response['result'] = result
        
        return response
    
    def create_jsonrpc_error(self, code: int, message: str, data: Any = None) -> Dict:
        """Create JSON-RPC 2.0 error object."""
        error = {
            'code': code,
            'message': message
        }
        if data is not None:
            error['data'] = data
        return error
    
    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle MCP initialize request."""
        return {
            'protocolVersion': self.protocol_version,
            'capabilities': {
                'tools': {}
            },
            'serverInfo': {
                'name': self.mcp_config['name'],
                'version': '1.0.0'
            }
        }
    
    async def handle_tools_list(self, params: Dict) -> Dict:
        """Handle tools/list request."""
        tools = self.get_mcp_tools()
        return {'tools': tools}
    
    async def handle_tools_call(self, params: Dict) -> Dict:
        """Handle tools/call request."""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        # Merge global MCP env vars with request env vars
        # Process global env vars list to extract defaults
        global_env_defaults = {}
        raw_env_vars = self.mcp_config.get('env_vars', [])
        
        # Backward compatibility if it's still a dict (should be migrated, but safe guard)
        if isinstance(raw_env_vars, dict):
             global_env_defaults = raw_env_vars
        elif isinstance(raw_env_vars, list):
            for item in raw_env_vars:
                if isinstance(item, dict) and item.get('name') and item.get('default_value'):
                     # Check Scope
                     scope = item.get('tool_ids', [])
                     if scope and tool_name not in scope:
                         continue
                         
                     global_env_defaults[item['name']] = item['default_value']

        request_env = params.get('env', {})
        
        # Combine: Start with global defaults, override/append with request
        final_env = {**global_env_defaults}
        if request_env:
            final_env.update(request_env)
        
        # Find tool
        tool = self.get_tool_by_id(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Check if tool is enabled for this MCP
        if tool_name not in self.mcp_config.get('tool_ids', []):
            raise ValueError(f"Tool not enabled for this MCP: {tool_name}")
        
        # Execute tool - collect output via streaming
        result_text = ""
        logs_text = ""
        exit_code = 0
        
        try:
            async for event in execution_service.execute_tool_stream(tool['path'], arguments, env=final_env):
                event_data = json.loads(event)
                if event_data['type'] == 'stdout':
                    result_text += event_data['data']
                elif event_data['type'] == 'stderr':
                    logs_text += event_data['data']
                elif event_data['type'] == 'exit':
                    exit_code = event_data['code']
        except Exception as e:
            raise ValueError(f"Tool execution failed: {str(e)}")
        
        # Format response in MCP format
        content = []
        
        # Add result as text
        if result_text:
            content.append({
                'type': 'text',
                'text': result_text
            })
        
        # Add logs if present and execution failed
        if logs_text and exit_code != 0:
            content.append({
                'type': 'text',
                'text': f"\n\n--- Logs ---\n{logs_text}"
            })
        
        return {
            'content': content,
            'isError': exit_code != 0
        }
    
    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming JSON-RPC 2.0 request."""
        try:
            # Validate JSON-RPC 2.0 format
            if request.get('jsonrpc') != '2.0':
                return self.create_jsonrpc_response(
                    None,
                    error=self.create_jsonrpc_error(
                        INVALID_REQUEST,
                        "Invalid JSON-RPC version"
                    )
                )
            
            request_id = request.get('id')
            method = request.get('method')
            params = request.get('params', {})
            
            if not method:
                return self.create_jsonrpc_response(
                    request_id,
                    error=self.create_jsonrpc_error(
                        INVALID_REQUEST,
                        "Method is required"
                    )
                )
            
            # Route to handler
            if method == 'initialize':
                result = await self.handle_initialize(params)
            elif method == 'tools/list':
                result = await self.handle_tools_list(params)
            elif method == 'tools/call':
                result = await self.handle_tools_call(params)
            else:
                return self.create_jsonrpc_response(
                    request_id,
                    error=self.create_jsonrpc_error(
                        METHOD_NOT_FOUND,
                        f"Method not found: {method}"
                    )
                )
            
            return self.create_jsonrpc_response(request_id, result=result)
            
        except ValueError as e:
            return self.create_jsonrpc_response(
                request.get('id'),
                error=self.create_jsonrpc_error(
                    INVALID_PARAMS,
                    str(e)
                )
            )
        except Exception as e:
            return self.create_jsonrpc_response(
                request.get('id'),
                error=self.create_jsonrpc_error(
                    INTERNAL_ERROR,
                    f"Internal error: {str(e)}"
                )
            )


async def mcp_sse_endpoint(
    mcp_id: str,
    request: Request,
    api_key: Optional[str] = None
) -> EventSourceResponse:
    """
    SSE endpoint for MCP protocol.
    
    This endpoint:
    1. Authenticates the client via API key
    2. Establishes SSE connection
    3. Waits for JSON-RPC 2.0 messages via POST to companion endpoint
    4. Sends responses back via SSE
    """
    
    # Authenticate
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if not mcp_manager.authenticate_mcp(mcp_id, api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    # Get MCP server instance
    try:
        mcp_server = MCPServer(mcp_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Record connection
    client_info = request.headers.get('user-agent', 'Unknown')
    connection_id = mcp_manager.record_connection(mcp_id, client_info)
    
    async def event_generator() -> AsyncGenerator[Dict, None]:
        """Generate SSE events."""
        try:
            # Send initial connection established event
            yield {
                'event': 'connected',
                'data': json.dumps({
                    'mcp_id': mcp_id,
                    'protocol_version': mcp_server.protocol_version
                })
            }

            # Critical: Tell client where to send POST messages
            yield {
                'event': 'endpoint',
                'data': f"/mcp/{mcp_id}/message"
            }
            
            # Keep connection alive with periodic pings
            # In real implementation, this would listen for incoming messages
            # For now, we'll use a different approach via POST endpoint
            while True:
                await asyncio.sleep(30)
                mcp_manager.update_connection_ping(connection_id)
                yield {
                    'event': 'ping',
                    'data': json.dumps({'timestamp': asyncio.get_event_loop().time()})
                }
                
        except asyncio.CancelledError:
            # Client disconnected
            mcp_manager.remove_connection(connection_id)
            raise
    
    return EventSourceResponse(event_generator())


async def mcp_message_endpoint(
    mcp_id: str,
    message: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict:
    """
    POST endpoint to send JSON-RPC messages to MCP.
    Returns JSON-RPC response immediately (not via SSE).
    
    This is a simpler alternative to full bidirectional SSE.
    """
    
    # Authenticate
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if not mcp_manager.authenticate_mcp(mcp_id, api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    # Get MCP server instance
    try:
        mcp_server = MCPServer(mcp_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Handle request
    response = await mcp_server.handle_request(message)
    return response
