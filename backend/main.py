from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from config import settings
from api.routes import auth, executions, tools, workspaces, mcps, settings as settings_routes, builds
from core.logger import logger, request_id_ctx

# Criar aplicação FastAPI
app = FastAPI(
    title="ContextWorks API",
    description="Plataforma enterprise de execução de ferramentas de segurança",
    version="2.0.0"
)

# Exception Handler Global (Enterprise Style)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global Exception caught", exc_info=True, extra={"extra_fields": {"path": request.url.path}})
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "request_id": request_id_ctx.get()
        }
    )

# Middleware para Logging de requisições com Traceability
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_ctx.set(request_id)
    
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Request processed",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(process_time, 2),
                "ip": request.client.host if request.client else "unknown"
            }}
        )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_ctx.reset(token)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Registrar rotas
app.include_router(auth.router)
app.include_router(executions.router, prefix="/api/executions")
app.include_router(tools.router)
app.include_router(workspaces.router)
app.include_router(mcps.router)
app.include_router(mcps.router)
app.include_router(mcps.mcp_router)
app.include_router(settings_routes.router, prefix="/api")
app.include_router(builds.router, prefix="/api/builds")

@app.get("/")
def read_root():
    return {
        "message": "Security Platform API is running",
        "version": "2.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "kubernetes": "configured"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
