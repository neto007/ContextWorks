import os
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, Optional
import time
import re
import shutil

from kubernetes import client, config, watch
import psycopg2.extras

from config import settings
from core import database, utils
from core.logger import logger
from services.docker.registry_adapter import construct_remote_tag
from services.docker.image_builder import ImageBuilderService

class KanikoBuilderService:
    def __init__(self):
        # Determine where to store temporary build contexts
        # In a real K8s deployment, this directory should be ephemeral or managed.
        self.temp_base = Path("/tmp/build-contexts")
        self.temp_base.mkdir(parents=True, exist_ok=True)

    def prepare_context(self, job_id: str, category: str, tool_name: str, docker_config: Dict) -> Optional[Path]:
        """
        Generates the build context and archives it into a .tar.gz file.
        Returns the path to the tarball.
        """
        # Create a temp directory for this build
        build_dir = Path(tempfile.mkdtemp(prefix=f"kaniko_ctx_{job_id}_"))
        
        try:
            # Use ImageBuilderService logic to generate Dockerfile and copy files
            # We pass the temp dir as the build root
            builder = ImageBuilderService(build_dir=build_dir)
            
            # We assume ImageBuilderService.generate_dockerfile is modular enough
            # We need to manually drive it because build_tool_image does the build too.
            # Reuse logic from ImageBuilderService.build_tool_image basically:
            
            # Context dir inside the temp root
            context_dir = build_dir / f"context"
            context_dir.mkdir(parents=True)
            
            # Generate Dockerfile
            dockerfile_content = builder.generate_dockerfile(tool_name, docker_config, context_dir)
            if not dockerfile_content:
                # If no content, maybe we can't build.
                logger.error("Failed to generate Dockerfile", extra={"extra_fields": {"tool_name": tool_name, "job_id": job_id}})
                return None
                
            (context_dir / "Dockerfile").write_text(dockerfile_content)
            
            # Now archive the context_dir
            tar_path = self.temp_base / f"{job_id}.tar.gz"
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(context_dir, arcname=".")
                
            logger.info("Context tarball created", extra={"extra_fields": {"job_id": job_id, "tar_path": str(tar_path), "size_bytes": tar_path.stat().st_size}})
            return tar_path
            
        except Exception as e:
            logger.error("Error preparing context for Kaniko", exc_info=True, extra={"extra_fields": {"job_id": job_id, "tool_name": tool_name}})
            return None
        finally:
            # Cleanup the uncompressed dir
            if build_dir.exists():
                shutil.rmtree(build_dir)

    def trigger_build(self, job_id: str, category: str, tool_name: str, docker_config: Dict):
        """
        Creates and submits a Kubernetes Job to run Kaniko.
        """
        # 1. Prepare Context
        database.append_build_logs(job_id, "📦 Preparing build context...\n")
        tar_path = self.prepare_context(job_id, category, tool_name, docker_config)
        
        if not tar_path:
            database.update_build_job(job_id, "FAILED")
            database.append_build_logs(job_id, "❌ Failed to prepare build context.\n")
            return

        # 2. Determine Destination
        # Default to internal registry if not configured
        registry_config = database.get_registry_config() or {"type": "internal"}
        
        # Calculate image tag
        image_tag = docker_config.get("image")
        if not image_tag or "security-platform-tool-" in image_tag:
             image_tag = utils.generate_image_tag(tool_name)
        
        # Determine destination string (Kaniko format)
        destination = ""
        if registry_config.get("type") in ["internal", "local"]:
             # image_tag from utils.generate_image_tag() already includes registry prefix
             # For Minikube/Dev, we might need to use a different internal hostname for PUSH
             # than what the K8s nodes use for PULL.
             push_registry = settings.DOCKER_REGISTRY_PUSH
             pull_registry = settings.DOCKER_REGISTRY
             
             if pull_registry in image_tag and push_registry != pull_registry:
                 destination = image_tag.replace(pull_registry, push_registry)
                 database.append_build_logs(job_id, f"📝 Adjusted destination for internal push: {destination}\n")
             else:
                 destination = image_tag
                 
             database.append_build_logs(job_id, f"🎯 Destination: Internal Registry ({destination})\n")
        else:
             # External Registry
             destination = construct_remote_tag(image_tag, registry_config)
             database.append_build_logs(job_id, f"🎯 Destination: {registry_config['type']} ({destination})\n")


        # 3. Backend Context URL
        # The Kaniko pod must reach this backend. 
        # In K8s, backend usually has a service.
        backend_host = os.getenv("BACKEND_INTERNAL_URL", f"http://{os.getenv('HOSTNAME')}:{settings.API_PORT}") 
        # Fallback if HOSTNAME is pod name, need SVC name. 
        # Usually user sets BACKEND_INTERNAL_URL.
        # If running in same namespace, "backend-service" often works.
        # For this implementation, let's assume `backend-service` or allow env override.
        if "://" not in backend_host:
            backend_host = f"http://{backend_host}"
            
        context_url = f"{backend_host}/api/builds/context/{job_id}"
        
        # 4. Create Job Def
        batch_v1 = client.BatchV1Api()
        
        job_name = f"kaniko-build-{job_id[:8]}"
        
        # Shared Volume for Context
        volume_mounts = [
            client.V1VolumeMount(
                name="workspace-vol",
                mount_path="/workspace"
            )
        ]
        
        volumes = [
            client.V1Volume(
                name="workspace-vol",
                empty_dir=client.V1EmptyDirVolumeSource()
            )
        ]
        
        # Init Container: Download and Extract Context
        # wget -O /tmp/context.tar.gz {url} && tar -xzf /tmp/context.tar.gz -C /workspace
        init_cmd = f"wget -q -O /tmp/context.tar.gz '{context_url}' && tar -xzf /tmp/context.tar.gz -C /workspace"
        
        init_container = client.V1Container(
            name="context-init",
            image="busybox:latest",
            command=["sh", "-c", init_cmd],
            volume_mounts=volume_mounts
        )

        # Kaniko Args - Always push to registry
        kaniko_args = [
            f"--dockerfile=Dockerfile",
            f"--context=dir:///workspace",
            f"--destination={destination}",
            "--force",
            "--insecure",
            "--skip-tls-verify"
        ]
        
        env_vars = []
        
        # Simple cleanup policy
        ttl_seconds = 600 # 10 mins after finish
        
        # Job Spec
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=job_name, namespace=settings.K8S_NAMESPACE),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=ttl_seconds,
                backoff_limit=0,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"job-type": "kaniko-build", "build-id": job_id}),
                    spec=client.V1PodSpec(
                        restart_policy="Never",
                        init_containers=[init_container],
                        containers=[
                            client.V1Container(
                                name="kaniko",
                                image="gcr.io/kaniko-project/executor:latest",
                                args=kaniko_args,
                                env=env_vars,
                                volume_mounts=volume_mounts
                            )
                        ],
                        volumes=volumes
                    )
                )
            )
        )
        
        try:
            logger.info("Launching Kaniko Build Job", extra={"extra_fields": {"job_name": job_name, "build_id": job_id, "tool_name": tool_name}})
            database.append_build_logs(job_id, f"🚀 Launching Kaniko Job: {job_name}\n")
            batch_v1.create_namespaced_job(namespace=settings.K8S_NAMESPACE, body=job)
            
            # Monitor Job
            self.monitor_job(job_id, job_name, batch_v1, destination)
            
        except Exception as e:
            logger.error("Failed to create Kaniko K8s Job", exc_info=True, extra={"extra_fields": {"job_id": job_id, "tool_name": tool_name}})
            database.update_build_job(job_id, "FAILED")
            database.append_build_logs(job_id, f"💥 Failed to create K8s Job: {e}\n")

    def monitor_job(self, job_id: str, job_name: str, batch_api, destination: str):
        """
        Polls the job status and streams logs to DB.
        """
        core_v1 = client.CoreV1Api()
        namespace = settings.K8S_NAMESPACE
        
        # Wait for pod and main container to start
        pod_name = None
        database.append_build_logs(job_id, "⏳ Waiting for builder pod to initialize...\n")
        
        start_time = time.time()
        while time.time() - start_time < 120:
            pods = core_v1.list_namespaced_pod(namespace, label_selector=f"job-name={job_name}")
            if pods.items:
                pod = pods.items[0]
                pod_name = pod.metadata.name
                
                # Check for Init Container Failures
                if pod.status.init_container_statuses:
                    for init_status in pod.status.init_container_statuses:
                        if init_status.state.terminated and init_status.state.terminated.exit_code != 0:
                            database.update_build_job(job_id, "FAILED")
                            init_logs = ""
                            try:
                                init_logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, container="context-init")
                            except:
                                init_logs = "Could not fetch init logs."
                            database.append_build_logs(job_id, f"❌ Init Container Failed: {init_status.state.terminated.reason}\nLogs:\n{init_logs}\n")
                            return

                # Check Main Container Status
                if pod.status.container_statuses:
                    for status in pod.status.container_statuses:
                        if status.name == "kaniko":
                            if status.state.running or status.state.terminated:
                                break # Ready to stream
                    else:
                        time.sleep(1)
                        continue # specific container not found or not ready
                    break # inner break triggered
            
            time.sleep(2)
            
        if not pod_name:
            database.update_build_job(job_id, "FAILED")
            database.append_build_logs(job_id, "❌ Timeout waiting for builder pod.\n")
            return

        # Stream Logs
        try:
            database.append_build_logs(job_id, f"📜 Streaming logs from {pod_name}...\n")
            
            # ANSI escape code regex
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            # Watch logs (blocking)
            w = watch.Watch()
            for e in w.stream(core_v1.read_namespaced_pod_log, name=pod_name, namespace=namespace, container="kaniko"):
                # Strip ANSI codes
                clean_line = ansi_escape.sub('', e)
                database.append_build_logs(job_id, f"[Kaniko] {clean_line}\n")
                
            # Wait a moment for Job status to update (Kubernetes needs time after pod completes)
            time.sleep(3)
            
            # Get all logs to check for success indicators
            all_logs = database.get_build_job(job_id).get('logs', '')
            
            # Check final status - Kaniko success is indicated by "Pushed" message
            job = batch_api.read_namespaced_job(job_name, namespace)
            build_succeeded = (job.status.succeeded and job.status.succeeded > 0) or ('Pushed' in all_logs and 'sha256:' in all_logs)
            
            if build_succeeded:
                database.update_build_job(job_id, "SUCCESS", image_tag=destination)
                database.append_build_logs(job_id, "\n✅ Build & Push Successful!\n")
            else:
                database.update_build_job(job_id, "FAILED")
                database.append_build_logs(job_id, "\n❌ Build Failed.\n")
                
        except Exception as e:
             database.append_build_logs(job_id, f"Error monitoring logs: {e}\n")
             # Try to check status one last time
             all_logs = database.get_build_job(job_id).get('logs', '')
             job = batch_api.read_namespaced_job(job_name, namespace)
             build_succeeded = (job.status.succeeded and job.status.succeeded > 0) or ('Pushed' in all_logs and 'sha256:' in all_logs)
             
             if build_succeeded:
                 database.update_build_job(job_id, "SUCCESS", image_tag=destination)
             else:
                 database.update_build_job(job_id, "FAILED")
        
        # Cleanup Context
        context_file = self.temp_base / f"{job_id}.tar.gz"
        if context_file.exists():
            context_file.unlink()

# Global Instance
kaniko_service = KanikoBuilderService()
