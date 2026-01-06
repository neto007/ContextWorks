import os
import subprocess
import yaml
import tempfile
import shutil
from pathlib import Path
from typing import Dict
from core import database
from core.logger import logger
from .registry_adapter import push_image_to_registry

REPO_ROOT = Path(__file__).parent.parent.parent.parent
BUILD_SCRIPT = REPO_ROOT / "docker" / "build-tool-images.py"

def run_build_thread(job_id: str, category: str, tool_name: str, docker_config: Dict):
    """
    Background worker for build process.
    Captures stdout/stderr and streams to database logs.
    """
    try:
        database.update_build_job(job_id, "RUNNING")
        
        env = os.environ.copy()
        env["AUTO_LOAD_K8S"] = "false"
        env["PYTHONUNBUFFERED"] = "1"
        
        database.append_build_logs(job_id, f"🚀 Starting build for {tool_name} (Job {job_id})\n")
        
        temp_dir = None
        try:
            full_tool_id = f"{category}/{tool_name}"
            tool_data = database.get_tool(full_tool_id)
            
            if not tool_data:
                database.append_build_logs(job_id, f"❌ Tool {full_tool_id} not found in database\n")
                database.update_build_job(job_id, "FAILED")
                return
            
            # Use Native ImageBuilderService
            from .image_builder import ImageBuilderService
            
            # We use a temporary directory for the build context
            temp_dir = Path(tempfile.mkdtemp(prefix=f"native_build_{tool_name}_"))
            builder = ImageBuilderService(build_dir=temp_dir)
            
            success, image_tag, build_logs = builder.build_tool_image(tool_name, docker_config, job_id)
            
            # Stream logs to DB
            database.append_build_logs(job_id, build_logs)
            
            if not success:
                database.update_build_job(job_id, "FAILED")
                database.append_build_logs(job_id, f"\n❌ Build process failed.\n")
                return

            database.append_build_logs(job_id, "\n📦 Build successful. Initiating image push/load sequence...\n")
            
            push_result = push_image_to_registry(tool_name, docker_config, job_id)
            
            if push_result['status'] == 'success':
                tag = push_result.get('image', 'unknown')
                msg = f"\n✅ Successfully {'loaded into ' + push_result['loaded_to'] + ' cluster' if 'loaded_to' in push_result else 'pushed to registry'}: {tag}\n"
                database.update_build_job(job_id, "SUCCESS", image_tag=tag)
                database.append_build_logs(job_id, msg)
            else:
                database.update_build_job(job_id, "FAILED")
                database.append_build_logs(job_id, f"\n❌ Push failed: {push_result.get('error')}\n")
        
        except Exception as e:
            database.append_build_logs(job_id, f"\n💥 Build service error: {str(e)}\n")
            database.update_build_job(job_id, "FAILED")
        finally:
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

    except Exception as e:
        logger.error("Async build error", exc_info=True, extra={"extra_fields": {"job_id": job_id, "tool_name": tool_name}})
        database.update_build_job(job_id, "FAILED")
        database.append_build_logs(job_id, f"\n💥 Internal System Error: {str(e)}\n")
