"""
Rotas de Workspaces (Categorias de Ferramentas)
"""
from fastapi import APIRouter, HTTPException, Response

from models.workspace import CreateWorkspaceRequest, UpdateWorkspaceRequest
from services import tool_service

router = APIRouter(prefix="/api/workspaces", tags=["Workspaces"])

@router.get("")
def list_workspaces():
    """Lista todos os workspaces com estatísticas"""
    return tool_service.list_categories()

@router.post("")
def create_workspace(request: CreateWorkspaceRequest):
    """Cria um novo workspace"""
    try:
        success = tool_service.create_category(request.name, request.description or "")
        if not success:
            raise HTTPException(status_code=400, detail="Workspace already exists")
        return {"status": "success", "name": request.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{name}")
def update_workspace(name: str, request: UpdateWorkspaceRequest):
    """Atualiza um workspace (rename ou descrição)"""
    try:
        success = tool_service.update_category(name, request.name, request.description, request.is_visible)
        if not success:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{name}")
def delete_workspace(name: str):
    """Deleta um workspace e todo seu conteúdo"""
    success = tool_service.delete_category(name)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"status": "success"}

@router.get("/{name}/logo")
def get_workspace_logo(name: str):
    """Obtém o logo de um workspace"""
    logo = tool_service.get_category_logo(name)
    if not logo:
        raise HTTPException(status_code=404, detail="Logo not found")
    return Response(content=logo, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})

@router.post("/{name}/logo")
def upload_workspace_logo(name: str, request: dict):
    """Faz upload do logo de um workspace"""
    svg_code = request.get("svg_code")
    if not svg_code:
        raise HTTPException(status_code=400, detail="svg_code is required")
    
    try:
        tool_service.save_category_logo(name, svg_code)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
