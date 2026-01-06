import os
import subprocess
from typing import Dict, Optional
from core import database, utils
from core.logger import logger

def push_image_to_registry(tool_name: str, docker_config: Dict, job_id: str = None) -> Dict:
    """
    Push built image to configured registry or load into local cluster.
    """
    def log(msg: str):
        if job_id:
            database.append_build_logs(job_id, f"{msg}\n")
        else:
            logger.info(msg)
    
    try:
        registry_config = database.get_registry_config() or {"type": "local", "use_local_fallback": True}
        
        # Use authoritative tag generation
        generated_tag = utils.generate_image_tag(tool_name)
        
        local_tag = docker_config.get("image")
        if not local_tag or "security-platform-tool-" in local_tag:
             local_tag = generated_tag
        
        if registry_config["type"] == "local":
            log(f"🔄 Auto-loading {local_tag} into local cluster...")
            return auto_load_to_k8s(local_tag, job_id)
        else:
            log(f"📤 Pushing {local_tag} to {registry_config['type']} registry...")
            if not docker_login(registry_config):
                if registry_config.get("use_local_fallback"):
                    log("⚠️ Registry login failed, falling back to local load")
                    return auto_load_to_k8s(local_tag, job_id)
                return {"status": "failed", "error": "Registry login failed"}
                
            target_tag = construct_remote_tag(local_tag, registry_config)
            subprocess.run(["docker", "tag", local_tag, target_tag], check=True)
            result = subprocess.run(["docker", "push", target_tag], capture_output=True, text=True)
            
            if result.returncode == 0:
                log(f"✅ Successfully pushed {target_tag}")
                return {"status": "success", "image": target_tag}
            else:
                error_msg = result.stderr
                log(f"❌ Push failed: {error_msg}")
                if registry_config.get("use_local_fallback"):
                    log("⚠️ Push failed, falling back to local load")
                    return auto_load_to_k8s(local_tag, job_id)
                return {"status": "failed", "error": f"Push failed: {error_msg}"}
                
    except Exception as e:
        log(f"❌ Error during image push: {e}")
        return {"status": "failed", "error": str(e)}

def docker_login(config: Dict) -> bool:
    try:
        if config["type"] == "dockerhub":
            if not config.get("username") or not config.get("password"):
                return False
            cmd = ["docker", "login", "-u", config["username"], "--password-stdin"]
            process = subprocess.run(cmd, input=config["password"], capture_output=True, text=True)
            return process.returncode == 0
        elif config["type"] == "ecr":
            cmd = f"aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {config.get('url')}"
            process = subprocess.run(cmd, shell=True, capture_output=True)
            return process.returncode == 0
        return True
    except Exception:
        return False

def construct_remote_tag(local_tag: str, config: Dict) -> str:
    image_part = local_tag.split("/")[-1]
    namespace = config.get("namespace")
    registry_url = config.get("url")
    
    if config["type"] == "dockerhub":
        return f"{namespace}/{image_part}" if namespace else image_part
    elif config["type"] in ["ecr", "gcr"] and registry_url:
        return f"{registry_url}/{namespace}/{image_part}" if namespace else f"{registry_url}/{image_part}"
    return local_tag

def auto_load_to_k8s(image_tag: str, job_id: str = None) -> Dict:
    def log(msg: str):
        if job_id:
            database.append_build_logs(job_id, f"{msg}\n")
        else:
            logger.info(msg)
    
    cluster_type = os.getenv("K8S_CLUSTER_TYPE", "minikube").lower()
    try:
        log(f"🔄 Loading {image_tag} into {cluster_type}...")
        if cluster_type == "minikube":
            subprocess.run(["minikube", "image", "load", image_tag], check=True, capture_output=True, text=True)
        elif cluster_type == "kind":
            subprocess.run(["kind", "load", "docker-image", image_tag], check=True, capture_output=True, text=True)
        log(f"✅ Successfully loaded into {cluster_type}")
        return {"status": "success", "image": image_tag, "loaded_to": cluster_type}
    except Exception as e:
        log(f"❌ Error loading image: {str(e)}")
        return {"status": "failed", "error": f"Failed to load into {cluster_type}: {str(e)}"}

def should_build_image(docker_config: Dict) -> bool:
    """
    Determine if a tool's docker config requires a build.
    """
    if not docker_config: 
        return False
        
    # Build if explicitly requested or if build-related keys are present
    has_build_config = any(k in docker_config for k in ["apt_packages", "pip_packages", "run_commands", "dockerfile", "base_image"])
    
    # Check for build mode (frontend uses 'custom')
    if docker_config.get("docker_mode") in ["build", "custom"]:
        return True
        
    # Check if image tag is internal (built by us)
    if "image" in docker_config and isinstance(docker_config["image"], str):
        return docker_config["image"].startswith("security-platform-tool-")
        
    return has_build_config
