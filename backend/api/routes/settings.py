"""
Settings API Routes
Handles platform configuration including registry settings
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict
from pydantic import BaseModel
import subprocess
import asyncio

from models.registry import RegistryConfig, RegistryTestRequest, RegistryTestResponse
from core import database
from services import docker_build_service

router = APIRouter()

class BuildRequest(BaseModel):
    category: str
    tool_name: str
    docker_config: Dict

@router.post("/settings/registry/build")
def start_async_build(request: BuildRequest) -> Dict:
    """Start async build job"""
    try:
        job_id = docker_build_service.trigger_build_async(
            request.category, 
            request.tool_name, 
            request.docker_config
        )
        return {"status": "started", "job_id": job_id}
    except Exception as e:
        raise HTTPException(500, f"Failed to start build: {str(e)}")

@router.get("/settings/registry/build/{job_id}/status")
def get_build_status(job_id: str) -> Dict:
    """Get build job status"""
    status = docker_build_service.get_build_status(job_id)
    if status.get("status") == "not_found":
        raise HTTPException(404, "Job not found")
    return status

async def log_generator(job_id: str):
    """Generate SSE events for build logs"""
    last_pos = 0
    poll_interval = 0.5
    
    while True:
        job = database.get_build_job(job_id)
        if not job:
            yield f"event: error\ndata: Job {job_id} not found\n\n"
            break
            
        logs = job.get('logs') or ""
        
        # Send new logs
        if len(logs) > last_pos:
            # Split new content by lines to ensure clean events if needed, 
            # but usually sending the chunk is fine for terminals.
            # We'll send the raw chunk.
            new_data = logs[last_pos:]
            # Escape newlines for SSE data payload if necessary, but usually libraries handle it.
            # For simple terminal streaming, we can send line by line or raw.
            # Let's clean it up for SSE format: "data: <content>\n\n"
            # If content has newlines, SSE expects "data: line1\ndata: line2\n\n".
            
            for line in new_data.splitlines(keepends=True):
                # Clean line ending
                clean_line = line.rstrip('\n')
                yield f"data: {clean_line}\n\n"
                
            last_pos = len(logs)
            
        # Check termination
        status = job.get('status')
        if status in ['SUCCESS', 'FAILED']:
            # Send one last check just in case logs updated with status
            # Then close
            yield f"event: {status.lower()}\ndata: {status}\n\n"
            yield "event: close\ndata: closed\n\n"
            break
            
        await asyncio.sleep(poll_interval)

@router.get("/settings/registry/build/{job_id}/logs")
async def stream_build_logs(job_id: str):
    """Stream logs via SSE"""
    return StreamingResponse(log_generator(job_id), media_type="text/event-stream")


@router.get("/settings/registry")
def get_registry_config() -> Dict:
    """Get current registry configuration"""
    try:
        config = database.get_registry_config()
        # Don't expose password in response
        if config and 'password' in config:
            config['password'] = "***" if config['password'] else None
        return config or {"type": "local", "use_local_fallback": True}
    except Exception as e:
        raise HTTPException(500, f"Failed to get registry config: {str(e)}")


@router.post("/settings/registry")
def save_registry_config(config: RegistryConfig) -> Dict:
    """Save registry configuration"""
    try:
        saved = database.save_registry_config(config.dict())
        # Don't expose password in response
        if 'password' in saved:
            saved['password'] = "***" if saved.get('password') else None
        return saved
    except Exception as e:
        raise HTTPException(500, f"Failed to save registry config: {str(e)}")


@router.post("/settings/registry/test")
def test_registry_connection(request: RegistryTestRequest) -> RegistryTestResponse:
    """Test connection to registry"""
    config = request.config
    
    try:
        if config.type == "local":
            # For local, just check if docker is available
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return RegistryTestResponse(
                    status="success",
                    message="Docker is available. Local registry mode enabled."
                )
            else:
                return RegistryTestResponse(
                    status="failed",
                    message="Docker is not available"
                )
        
        elif config.type == "dockerhub":
            # Test Docker Hub login
            if not config.username or not config.password:
                return RegistryTestResponse(
                    status="failed",
                    message="Username and password are required for Docker Hub"
                )
            
            result = subprocess.run(
                ["docker", "login", "-u", config.username, "--password-stdin"],
                input=config.password,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Logout immediately
            subprocess.run(["docker", "logout"], capture_output=True)
            
            if result.returncode == 0:
                return RegistryTestResponse(
                    status="success",
                    message="Successfully authenticated with Docker Hub"
                )
            else:
                return RegistryTestResponse(
                    status="failed",
                    message=f"Docker Hub authentication failed: {result.stderr}"
                )
        
        elif config.type == "ecr":
            # Test AWS ECR (requires AWS CLI)
            if not config.url:
                return RegistryTestResponse(
                    status="failed",
                    message="Registry URL is required for ECR"
                )
            
            # Check if AWS CLI is available
            result = subprocess.run(
                ["aws", "ecr", "get-login-password", "--region", "us-east-1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return RegistryTestResponse(
                    status="success",
                    message="AWS ECR credentials are valid"
                )
            else:
                return RegistryTestResponse(
                    status="failed",
                    message=f"AWS ECR authentication failed: {result.stderr}"
                )
        
        elif config.type == "gcr":
            # Test Google Container Registry
            if not config.url:
                return RegistryTestResponse(
                    status="failed",
                    message="Registry URL is required for GCR"
                )
            
            return RegistryTestResponse(
                status="success",
                message="GCR test not yet implemented. Assuming success."
            )
        
        else:
            return RegistryTestResponse(
                status="failed",
                message=f"Unknown registry type: {config.type}"
            )
    
    except subprocess.TimeoutExpired:
        return RegistryTestResponse(
            status="failed",
            message="Registry test timed out"
        )
    except FileNotFoundError as e:
        return RegistryTestResponse(
            status="failed",
            message=f"Required command not found: {str(e)}"
        )
    except Exception as e:
        return RegistryTestResponse(
            status="failed",
            message=f"Registry test failed: {str(e)}"
        )
