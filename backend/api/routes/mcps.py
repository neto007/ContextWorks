"""
Rotas de MCP Servers (Model Context Protocol)
"""
from fastapi import APIRouter, HTTPException, Response, Request, Header
from typing import Dict, Any, Optional

from models.mcp import MCPCreateRequest, MCPUpdateRequest
from services import mcp_manager, mcp_server

router = APIRouter(prefix="/api/mcps", tags=["MCP Servers"])

@router.get("")
def list_mcp_servers():
    """Lista todos os servidores MCP"""
    try:
        servers = mcp_manager.list_mcp_servers()
        return servers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def create_mcp_server(request: MCPCreateRequest):
    """Cria um novo servidor MCP"""
    try:
        mcp = mcp_manager.create_mcp_server(
            name=request.name,
            description=request.description,
            tool_ids=request.tool_ids,
            env_vars=[e.dict() for e in request.env_vars] if request.env_vars else []
        )
        return {
            "status": "success",
            "mcp": mcp,
            "api_key": mcp.get("api_key"),
            "note": "Save this API key - it won't be shown again"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{mcp_id}")
def get_mcp_server(mcp_id: str):
    """Obtém detalhes de um servidor MCP"""
    try:
        mcp = mcp_manager.get_mcp_server(mcp_id)
        if not mcp:
            raise HTTPException(status_code=404, detail="MCP server not found")
        return mcp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{mcp_id}")
def update_mcp_server(mcp_id: str, request: MCPUpdateRequest):
    """Atualiza um servidor MCP"""
    try:
        success = mcp_manager.update_mcp_server(
            mcp_id=mcp_id,
            name=request.name,
            description=request.description,
            tool_ids=request.tool_ids,
            status=request.status,
            env_vars=[e.dict() for e in request.env_vars] if request.env_vars is not None else None
        )
        if not success:
            raise HTTPException(status_code=404, detail="MCP server not found")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{mcp_id}")
def delete_mcp_server(mcp_id: str):
    """Deleta um servidor MCP"""
    try:
        success = mcp_manager.delete_mcp_server(mcp_id)
        if not success:
            raise HTTPException(status_code=404, detail="MCP server not found")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mcp_id}/regenerate-key")
def regenerate_mcp_api_key(mcp_id: str):
    """Regenera a API key de um servidor MCP"""
    try:
        new_key = mcp_manager.regenerate_api_key(mcp_id)
        if not new_key:
            raise HTTPException(status_code=404, detail="MCP server not found")
        return {"status": "success", "api_key": new_key, "note": "Save this API key - it won't be shown again"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{mcp_id}/logo")
def get_mcp_logo(mcp_id: str):
    """Obtém o logo de um servidor MCP"""
    logo = mcp_manager.get_mcp_logo(mcp_id)
    if not logo:
        raise HTTPException(status_code=404, detail="Logo not found")
    return Response(content=logo, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})

@router.post("/{mcp_id}/logo")
def upload_mcp_logo(mcp_id: str, request: Dict):
    """Faz upload do logo de um servidor MCP"""
    svg_code = request.get("svg_code")
    if not svg_code:
        raise HTTPException(status_code=400, detail="svg_code is required")
    
    try:
        mcp_manager.save_mcp_logo(mcp_id, svg_code)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MCP Protocol Endpoints (SSE e Messaging)
mcp_router = APIRouter(prefix="/mcp", tags=["MCP Protocol"])

@mcp_router.get("/{mcp_id}/sse")
async def mcp_sse(
    mcp_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    SSE endpoint para protocolo MCP.
    Autenticação via Authorization header: Bearer <api_key>
    """
    # Extrai API key do Authorization header
    api_key = None
    if authorization and authorization.startswith('Bearer '):
        api_key = authorization[7:]  # Remove 'Bearer ' prefix
    
    return await mcp_server.mcp_sse_endpoint(mcp_id, request, api_key)

@mcp_router.post("/{mcp_id}/message")
async def mcp_message(
    mcp_id: str,
    message: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    POST endpoint para enviar mensagens JSON-RPC 2.0 ao MCP.
    Retorna resposta imediatamente (mais simples que SSE bidirecional).
    Autenticação via Authorization header: Bearer <api_key>
    """
    # Extrai API key do Authorization header
    api_key = None
    if authorization and authorization.startswith('Bearer '):
        api_key = authorization[7:]
    
    return await mcp_server.mcp_message_endpoint(mcp_id, message, api_key)
