"""
Rotas de Ferramentas (Tools)
Refactored for Phase 3: Total DB Persistence
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import uuid
from typing import Dict
import os
import json
import yaml

from core.logger import logger

from models.tool import (
    CreateToolRequest,
    UpdateToolRequest,
    ToolContentRequest,
    LogoUploadRequest,
    TestToolRequest
)
from services import tool_service, execution_service
from core import database

router = APIRouter(prefix="/api/tools", tags=["Tools"])

@router.get("")
def list_tools():
    """Lista todas as ferramentas agrupadas por categoria"""
    return tool_service.scan_tools()

@router.get("/{category}/{tool_id}")
def get_tool_details(category: str, tool_id: str):
    """Obtém metadados de uma ferramenta específica"""
    full_id = f"{category}/{tool_id}"
    tool = database.get_tool(full_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    tools_dir = tool_service.TOOLS_BASE_DIR
    
    expanded = tool_service.expand_tool_config(dict(tool))
    
    return {
        "id": tool_id,
        "full_id": full_id,
        "name": expanded['name'],
        "category": expanded['category'],
        # Virtual paths for editor compatibility
        "path": os.path.join(tools_dir, category, f"{tool_id}.py"),
        "yaml_path": os.path.join(tools_dir, category, f"{tool_id}.yaml"),
        "description": expanded.get('description', ""),
        "script_code": expanded['script_code'],
        "arguments": expanded.get('arguments', []),
        "configuration": expanded.get('configuration', ""),
        "docker": expanded.get('docker'),
        "resources": expanded.get('resources'),
        "has_logo": database.get_logo('tool', full_id) is not None
    }

@router.post("")
def create_tool(payload: CreateToolRequest):
    """Cria uma nova ferramenta"""
    try:
        tool = tool_service.create_tool(payload.category, payload.dict())
        return {"status": "success", "tool": tool}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test")
async def test_tool(payload: TestToolRequest):
    """Testa uma ferramenta sem salvá-la (Dry Run)"""
    script_code = payload.script_code
    arguments = payload.arguments or {}
    
    # Prepare ad-hoc tool data
    req_tool_name = payload.tool_name or "test-tool"
    
    # Construct configuration
    config_yaml = payload.configuration or ""
    if payload.image and not config_yaml:
        config_yaml = yaml.dump({
            "docker": {
                "base_image": payload.image
            }
        })
    
    tool_data = {
        "id": payload.tool_id,
        "name": req_tool_name,
        "script_code": script_code,
        "configuration": config_yaml,
        "_is_test_mode": True
    }
    
    logger.info("Testing tool with job stream", extra={"extra_fields": {"tool_name": req_tool_name, "job_id": job_id}})
    return StreamingResponse(
        execution_service.run_tool_k8s_job_stream(tool_data, arguments, job_id),
        media_type="application/x-ndjson"
    )

@router.put("/{category}/{tool_id}")
def update_tool(category: str, tool_id: str, request: UpdateToolRequest):
    """Atualiza uma ferramenta existente"""
    try:
        tool = tool_service.update_tool(category, tool_id, request.dict(exclude_unset=True))
        return {"status": "success", "tool": tool}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{category}/{tool_id}")
def delete_tool(category: str, tool_id: str):
    """Deleta uma ferramenta"""
    success = tool_service.delete_tool(category, tool_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "success"}

@router.get("/{category}/{tool_id}/logo")
def get_tool_logo(category: str, tool_id: str):
    """Obtém o logo de uma ferramenta ou retorna placeholder"""
    logo = tool_service.get_tool_logo(category, tool_id)
    if not logo:
        # Retornar SVG placeholder ao invés de 404
        placeholder_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#6272a4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="9" x2="15" y2="15"></line>
            <line x1="15" y1="9" x2="9" y2="15"></line>
        </svg>'''
        return Response(content=placeholder_svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})
    return Response(content=logo, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})

@router.post("/{category}/{tool_id}/logo")
def upload_tool_logo(category: str, tool_id: str, payload: LogoUploadRequest):
    """Faz upload do logo de uma ferramenta"""
    svg_code = payload.svg_code
    if not svg_code:
        raise HTTPException(status_code=400, detail="svg_code is required")
    
    tool_service.save_tool_logo(category, tool_id, svg_code)
    return {"status": "success"}

@router.delete("/{category}/{tool_id}/logo")
def delete_tool_logo(category: str, tool_id: str):
    """Deleta o logo de uma ferramenta"""
    full_id = f"{category}/{tool_id}"
    database.delete_logo('tool', full_id)
    return {"status": "success", "message": "Logo deleted"}

# File content endpoints (DB ONLY)
@router.get("/content")
def get_file_content(path: str = None, tool_id: str = None, file_type: str = "py"):
    """Lê o conteúdo de uma ferramenta pelo ID do banco (ou infere do path)"""
    target_id = tool_id or tool_service.resolve_tool_id_from_path(path)
    if not target_id:
        raise HTTPException(status_code=400, detail="tool_id or valid path is required")
        
    try:
        content = tool_service.get_tool_content(target_id, file_type, path)
        return {"content": content}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/content")
def save_file_content(request: ToolContentRequest):
    """Salva conteúdo APENAS no banco de dados"""
    target_id = request.tool_id or tool_service.resolve_tool_id_from_path(request.path)
    if not target_id:
        raise HTTPException(status_code=400, detail="tool_id or valid path is required")
        
    try:
        changed = tool_service.save_tool_content(target_id, request.content, request.path)
        return {"status": "success", "changed": changed}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{category}/{tool_id}/build")
def trigger_tool_build(category: str, tool_id: str):
    """Dispara manualmente o build Docker de uma ferramenta"""
    full_id = f"{category}/{tool_id}"
    tool = database.get_tool(full_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Expand config to check docker settings
    expanded = tool_service.expand_tool_config(dict(tool))
    docker_config = expanded.get('docker')
    
    if not docker_config:
         raise HTTPException(status_code=400, detail="Tool has no docker configuration associated")
         
    try:
        from services.docker_build_service import trigger_build_async
        job_id = trigger_build_async(category, tool_id, docker_config)
        return {"status": "success", "job_id": job_id, "message": "Build started"}
    except Exception as e:
        logger.error("Error triggering manual build", exc_info=True, extra={"extra_fields": {"tool_id": tool_id, "category": category}})
        raise HTTPException(status_code=500, detail=f"Failed to trigger build: {str(e)}")
