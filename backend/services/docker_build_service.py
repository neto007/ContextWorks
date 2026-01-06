"""
Docker Build Service - Coordinator
Integrates modular build engine and registry adapter.
Refactored for Triplo Check: Modularized.
"""
import subprocess
import os
import threading
from typing import Dict, Optional
from pathlib import Path
from core.logger import logger

# Modular imports
from .docker.registry_adapter import push_image_to_registry, should_build_image as _should_build_base
from .docker.build_engine import run_build_thread, BUILD_SCRIPT

# Re-exporting for backward compatibility
should_build_image = _should_build_base

def trigger_build(category: str, tool_name: str, docker_config: Dict) -> Dict:
    """
    Trigger Docker image build for a tool (synchronous).
    """
    try:
        env = os.environ.copy()
        env["AUTO_LOAD_K8S"] = "false" 
        
        logger.info("Starting synchronous docker build", extra={"extra_fields": {"tool_name": tool_name}})
        
        result = subprocess.run(
            ["python3", str(BUILD_SCRIPT), "--tools", tool_name],
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )
        
        if result.returncode != 0:
            return {
                "status": "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        push_result = push_image_to_registry(tool_name, docker_config)
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "push_result": push_result
        }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "stderr": "Build timeout exceeded (5 minutes)", "returncode": -1}
    except Exception as e:
        return {"status": "failed", "stderr": str(e), "returncode": -1}

def trigger_build_async(category: str, tool_name: str, docker_config: Dict) -> str:
    """
    Trigger Docker image build for a tool (asynchronous).
    Uses Kaniko if running in K8s, otherwise local Docker.
    """
    from core import database
    job_id = database.create_build_job(f"{category}/{tool_name}")
    
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        # Kubernetes Environment: Use Kaniko
        from .docker.kaniko_builder import kaniko_service
        thread = threading.Thread(
            target=kaniko_service.trigger_build,
            args=(job_id, category, tool_name, docker_config)
        )
    else:
        # Local Environment: Use Docker Socket
        thread = threading.Thread(
            target=run_build_thread,
            args=(job_id, category, tool_name, docker_config)
        )
        
    thread.daemon = True
    thread.start()
    
    return job_id

def get_build_status(job_id: str) -> Dict:
    """
    Get status of an async build job.
    """
    from core import database
    job = database.get_build_job(job_id)
    if not job:
        return {"status": "not_found"}
        
    return {
        "job_id": job['id'],
        "tool_id": job['tool_id'],
        "status": job['status'],
        "logs": job['logs'],
        "created_at": job['created_at'],
        "updated_at": job['updated_at'],
        "image_tag": job.get('image_tag')
    }

# Fix exported should_build_image logic if it was different
def should_build_image(docker_config: Dict) -> bool:
    if not docker_config: return False
    has_build_config = any(k in docker_config for k in ["apt_packages", "pip_packages", "run_commands", "dockerfile", "base_image"])
    if "image" in docker_config:
        return docker_config["image"].startswith("security-platform-tool-")
    return has_build_config
