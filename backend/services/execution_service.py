import os
import json
import asyncio
import uuid
import time
from typing import Dict, Any, AsyncGenerator, Union, Optional

from core import database, kubernetes as k8s_core, utils
from core.logger import logger
from config import settings
from kubernetes import client

# Import modular components
from .execution.resolver import resolve_tool
from .execution.k8s_adapter import create_k8s_job, delete_k8s_job, parse_result_from_logs

# Load K8s Config using core module
k8s_core.setup_kubernetes()
K8S_NAMESPACE = settings.K8S_NAMESPACE

# ============================================================================
# EXECUTION LOGIC
# ============================================================================

def run_tool_script(tool_identifier_or_data: Union[str, Dict[str, Any]], args: Dict[str, Any], env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Executes a tool synchronousy.
    """
    job_id = str(uuid.uuid4())
    return run_tool_k8s_job_sync(tool_identifier_or_data, args, job_id, env)

def run_tool_k8s_job_sync(tool_identifier_or_data: Union[str, Dict], args: Dict[str, Any], job_id: str, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    # Resolve tool if string
    if isinstance(tool_identifier_or_data, str):
        try:
            tool_data = resolve_tool(tool_identifier_or_data)
        except Exception as e:
            return {"result": None, "logs": str(e), "exit_code": -1}
    else:
        tool_data = tool_identifier_or_data

    tool_name = tool_data.get('name', 'adhoc-tool')
    tool_name_safe = utils.sanitize_k8s_name(tool_name)
    job_name = f"{tool_name_safe}-{job_id}"
    
    # Create execution record
    database.create_execution(job_id, tool_name, tool_identifier_or_data if isinstance(tool_identifier_or_data, str) else tool_name, args, status="running")
    
    try:
        create_k8s_job(tool_data, args, job_name, job_id, env)
        
        batch_v1 = client.BatchV1Api()
        core_v1 = client.CoreV1Api()
        
        logger.info("Waiting for K8s Job completion", extra={"extra_fields": {"job_name": job_name, "timeout": settings.K8S_JOB_TIMEOUT_SECONDS}})
        for _ in range(settings.K8S_JOB_TIMEOUT_SECONDS):
            try:
                job = batch_v1.read_namespaced_job(name=job_name, namespace=K8S_NAMESPACE)
            except client.exceptions.ApiException:
                time.sleep(1)
                continue

            if job.status.succeeded:
                pod_list = core_v1.list_namespaced_pod(namespace=K8S_NAMESPACE, label_selector=f"job-name={job_name}")
                if not pod_list.items:
                    time.sleep(1)
                    pod_list = core_v1.list_namespaced_pod(namespace=K8S_NAMESPACE, label_selector=f"job-name={job_name}")
                    if not pod_list.items:
                        database.update_execution(job_id, status="failed", logs="Pod not found")
                        return {"result": None, "logs": "Pod not found", "exit_code": -1}
                
                pod_name = pod_list.items[0].metadata.name
                logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=K8S_NAMESPACE)
                delete_k8s_job(job_name)
                result = parse_result_from_logs(logs)
                database.update_execution(job_id, status="success", logs=logs, result=json.dumps(result) if result else "")
                return {"result": result, "logs": logs, "exit_code": 0}
            
            if job.status.failed:
                logs = "Job failed"
                try:
                    pod_list = core_v1.list_namespaced_pod(namespace=K8S_NAMESPACE, label_selector=f"job-name={job_name}")
                    if pod_list.items:
                        pod_name = pod_list.items[0].metadata.name
                        logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=K8S_NAMESPACE)
                except: pass
                delete_k8s_job(job_name)
                database.update_execution(job_id, status="failed", logs=logs)
                return {"result": None, "logs": logs, "exit_code": 1}
                
            time.sleep(1)
        
        database.update_execution(job_id, status="failed", logs="Timeout")
        return {"result": None, "logs": "Timeout", "exit_code": -1}
    except Exception as e:
        database.update_execution(job_id, status="failed", logs=str(e))
        return {"result": None, "logs": str(e), "exit_code": -1}

async def execute_tool_stream(tool_identifier_or_data: Union[str, Dict[str, Any]], args: Dict[str, Any], job_id: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> AsyncGenerator[str, None]:
    """
    Executes a tool as a K8s Job and streams output.
    """
    if isinstance(tool_identifier_or_data, str):
        try:
            tool_data = resolve_tool(tool_identifier_or_data)
        except Exception as e:
            yield json.dumps({"type": "stderr", "data": f"Resolution Error: {str(e)}"}) + "\n"
            yield json.dumps({"type": "exit", "code": 1}) + "\n"
            return
    else:
        tool_data = tool_identifier_or_data

    if not job_id:
        job_id = str(uuid.uuid4())
        
    logger.info("Starting execution stream", extra={"extra_fields": {"job_id": job_id, "tool": str(tool_identifier_or_data)}})
    
    tool_name = tool_data.get('name', 'adhoc-tool')
    tool_name_safe = utils.sanitize_k8s_name(tool_name)
    job_name = f"{tool_name_safe}-{job_id}"
    
    yield json.dumps({"type": "start", "id": job_id}) + "\n"
    
    # Check if job already exists (Re-attach mode)
    batch_v1 = client.BatchV1Api()
    loop = asyncio.get_running_loop()
    existing_jobs = await loop.run_in_executor(
        None, 
        lambda: batch_v1.list_namespaced_job(namespace=K8S_NAMESPACE, label_selector=f"execution-id={job_id}")
    )
    is_reattach = len(existing_jobs.items) > 0
    
    if is_reattach:
        logger.info("Re-attaching to existing execution", extra={"extra_fields": {"job_id": job_id, "job_name": existing_jobs.items[0].metadata.name}})
        job_name = existing_jobs.items[0].metadata.name
    else:
        # Construct absolute path for DB (to match frontend filtering)
        tool_path_for_db = tool_identifier_or_data if isinstance(tool_identifier_or_data, str) else tool_name
        
        if isinstance(tool_data, dict) and 'category' in tool_data and 'id' in tool_data:
            try:
                # id is usually "Category/tool_id"
                short_id = tool_data['id'].split('/')[-1]
                tool_path_for_db = os.path.join(settings.TOOLS_BASE_DIR, tool_data['category'], f"{short_id}.py")
            except:
                 pass

        database.create_execution(job_id, tool_name, tool_path_for_db, args, status="running")

    try:
        if not is_reattach:
            await loop.run_in_executor(None, lambda: create_k8s_job(tool_data, args, job_name, job_id, env))
        core_v1 = client.CoreV1Api()
        
        pod_name = None
        for _ in range(settings.K8S_POD_WAIT_ASYNC_SECONDS):
            pods = await loop.run_in_executor(None, lambda: core_v1.list_namespaced_pod(
                namespace=K8S_NAMESPACE, label_selector=f"job-name={job_name}"
            ))
            if pods.items:
                pod_name = pods.items[0].metadata.name
                break
            await asyncio.sleep(1)
            
        if not pod_name:
            yield json.dumps({"type": "stderr", "data": "Timeout waiting for pod"}) + "\n"
            database.update_execution(job_id, status="failed", logs="Timeout waiting for pod")
            return

        last_log_pos = 0
        acc_logs, acc_result = "", ""
        
        while True:
            try:
                pod = await loop.run_in_executor(None, lambda: core_v1.read_namespaced_pod(name=pod_name, namespace=K8S_NAMESPACE))
            except Exception as e:
                # Pod might not be ready or API error
                break

            try:
                full_logs = await loop.run_in_executor(None, lambda: core_v1.read_namespaced_pod_log(name=pod_name, namespace=K8S_NAMESPACE))
                if len(full_logs) > last_log_pos:
                    chunk = full_logs[last_log_pos:]
                    yield json.dumps({"type": "stderr", "data": chunk}) + "\n"
                    last_log_pos = len(full_logs)
                    acc_logs = full_logs
            except: 
                pass
            
            if pod.status.phase in ["Succeeded", "Failed"]:
                break
            await asyncio.sleep(1)
            
        exit_code = 0 if pod.status.phase == "Succeeded" else 1
        yield json.dumps({"type": "exit", "code": exit_code}) + "\n"
        
        if "--- RESULT ---" in acc_logs:
            acc_result = acc_logs.split("--- RESULT ---")[-1].strip()
            yield json.dumps({"type": "stdout", "data": acc_result}) + "\n"
        else:
            lines = acc_logs.strip().split('\n')
            if lines and exit_code == 0:
                for line in reversed(lines):
                    line = line.strip()
                    if (line.startswith('{') and line.endswith('}')) or (line.startswith('[') and line.endswith(']')):
                         acc_result = line
                         yield json.dumps({"type": "stdout", "data": acc_result}) + "\n"
                         break

        database.update_execution(job_id, status="success" if exit_code == 0 else "failed", logs=acc_logs, result=acc_result)
        await loop.run_in_executor(None, lambda: delete_k8s_job(job_name))

    except Exception as e:
        err_msg = str(e)
        yield json.dumps({"type": "stderr", "data": f"Error: {err_msg}"}) + "\n"
        yield json.dumps({"type": "exit", "code": 1}) + "\n"
        database.update_execution(job_id, status="failed", logs=err_msg)

def stop_execution(job_id: str):
    """Parses jobs to find the correct one by label."""
    try:
        batch_v1 = client.BatchV1Api()
        jobs = batch_v1.list_namespaced_job(namespace=K8S_NAMESPACE, label_selector=f"execution-id={job_id}")
        if jobs.items:
            for job in jobs.items:
                delete_k8s_job(job.metadata.name)
        else:
            delete_k8s_job(f"exec-{job_id}")
    except: pass
        
    database.update_execution(job_id, status="stopped", logs="\n[Stopped by user]")
    return True

def get_live_logs(job_id: str) -> str:
    """
    Fetches logs for a job.
    1. Checks if K8s pod exists -> return live logs key
    2. Fallback to DB logs
    """
    # Try finding the pod first (if running)
    try:
        from core.logger import logger
        core_v1 = client.CoreV1Api()
        # Search by label job-name which we construct as tool_safe-job_id
        # Actually we can search by our custom label if we added it, but we didn't. 
        # But we know the job_name pattern. However, easier to search by the label selector used in wait.
        # We don't easily know tool name here without DB query.
        
        # Better strategy: Get execution from DB to know status and tool name
        execution = database.get_execution(job_id)
        if not execution:
            return "Execution not found."
            
        if execution['status'] == 'running':
            # Try to find pod matching the job
            # We don't store job_name in DB, but we can try to find by label if we add it,
            # or reconstruct.
            # Let's try listing pods with the label "job-name" where the name contains the ID
            # This is a bit loose but workable.
            
            # Actually, we can list jobs by label "execution-id" if we tagged them?
            # We tagged jobs with arguments? No.
            
            # Let's inspect create_k8s_job to see if we can add a label "execution-id"
            # Modifying create_k8s_job is safer for future. 
            # For now, let's use the method that `stop_execution` uses:
            
            batch_v1 = client.BatchV1Api()
            jobs = batch_v1.list_namespaced_job(namespace=K8S_NAMESPACE, label_selector=f"execution-id={job_id}")
            
            if jobs.items:
                job_name = jobs.items[0].metadata.name
                # Now get pod
                pods = core_v1.list_namespaced_pod(namespace=K8S_NAMESPACE, label_selector=f"job-name={job_name}")
                if pods.items:
                    pod_name = pods.items[0].metadata.name
                    return core_v1.read_namespaced_pod_log(name=pod_name, namespace=K8S_NAMESPACE)
    except Exception as e:
        logger.error("Error fetching live logs from K8s", exc_info=True, extra={"extra_fields": {"job_id": job_id}})
        pass
        
    # Fallback to DB
    execution = database.get_execution(job_id)
    if execution:
        return execution.get('logs', '')
        
    return "Logs unavailable."

# Compatibility Aliases
run_tool_k8s_job_stream = execute_tool_stream

