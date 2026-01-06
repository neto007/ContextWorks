from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
import os
from core.logger import logger

router = APIRouter(tags=["Builds"])

TEMP_BUILD_DIR = Path("/tmp/build-contexts")

@router.get("/context/{job_id}")
def get_build_context(job_id: str, background_tasks: BackgroundTasks):
    """
    Serves the build context tarball for a specific job.
    Called by Kaniko inside the cluster.
    """
    tar_path = TEMP_BUILD_DIR / f"{job_id}.tar.gz"
    
    if not tar_path.exists():
        logger.warning("Build context not found", extra={"extra_fields": {"job_id": job_id}})
        raise HTTPException(status_code=404, detail="Context not found")
        
    logger.info("Serving build context", extra={"extra_fields": {"job_id": job_id}})
    
    # We explicitly do NOT delete it here immediately because Kaniko might retry or connection might break.
    # Cleanup is handled by the builder service after job completion.
    
    return FileResponse(
        path=tar_path,
        media_type="application/gzip",
        filename=f"context-{job_id}.tar.gz"
    )
