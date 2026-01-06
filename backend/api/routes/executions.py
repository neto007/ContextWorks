"""
Rotas de Execuções de Ferramentas
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.tool import ToolExecutionRequest
from services import execution_service
from core import database

router = APIRouter(tags=["Executions"])

@router.post("/execute")
def execute_tool(request: ToolExecutionRequest):
    """Executa uma ferramenta de forma síncrona"""
    identifier = request.tool_id or request.path
    if not identifier:
        raise HTTPException(status_code=400, detail="tool_id or path required")

    output = execution_service.run_tool_script(identifier, request.arguments)
    return {"output": output}

@router.post("/execute/stream")
async def execute_tool_stream(request: ToolExecutionRequest):
    """Executa uma ferramenta e retorna stream de logs"""
    identifier = request.tool_id or request.path
    if not identifier:
        raise HTTPException(status_code=400, detail="tool_id or path required")

    return StreamingResponse(
        execution_service.execute_tool_stream(identifier, request.arguments, request.job_id),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"}
    )

@router.post("/execute/stop/{job_id}")
def stop_tool_execution(job_id: str):
    """Para a execução de uma ferramenta"""
    execution_service.stop_execution(job_id)
    return {"status": "success", "message": "Execution stopped"}

@router.get("/execute/{job_id}/logs")
def get_execution_logs(job_id: str):
    """Obtém logs ao vivo (ou finalizados) de uma execução"""
    logs = execution_service.get_live_logs(job_id)
    return {"logs": logs}

@router.get("/stats")
def get_execution_statistics():
    """Retorna estatísticas agregadas de execuções e da plataforma"""
    execution_stats = database.get_execution_stats()
    platform_stats = database.get_platform_stats()
    
    return {
        "executions": execution_stats,
        "platform": platform_stats
    }

@router.get("")
def list_executions(limit: int = 50):
    """Lista execuções recentes"""
    return database.get_executions(limit)

@router.get("/{execution_id}")
def get_execution(execution_id: str):
    """Obtém detalhes de uma execução específica"""
    execution = database.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
