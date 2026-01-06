
import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from core.logger import logger
from core import utils

class ImageBuilderService:
    """
    Native backend service for building Tool Docker images.
    Replaces the external docker/build-tool-images.py script.
    """
    
    def __init__(self, build_dir: Path):
        self.build_root_dir = build_dir
        self.build_root_dir.mkdir(parents=True, exist_ok=True)

    def generate_dockerfile(self, tool_name: str, docker_config: Dict, context_path: Path) -> Optional[str]:
        """Generate Dockerfile content based on configuration"""
        
        # Option 1: Use existing image (no build needed)
        has_build_config = any(k in docker_config for k in ["apt_packages", "pip_packages", "run_commands", "dockerfile", "base_image"])
        if "image" in docker_config and not has_build_config:
            return None  # Will use pre-existing image
        
        # Option 2: Custom Dockerfile provided
        if "dockerfile" in docker_config:
            # We expect the dockerfile path to be relative to the repository root
            # Since we are in backend service, we need to resolve it effectively.
            # However, usually docker_config['dockerfile'] is path from repo root.
            # We might need to adjust this logic if users provide paths.
            # For now, we assume simple paths or handle content directly if passed.
            
            # If it's a path, try to read it.
            # CAUTION: This assumes the backend has access to the repo structure if it's a relative path.
            # In the previous script REPO_ROOT was defined. Here we might need to be careful.
            # FOR NOW: Let's assume standard auto-generation mostly. 
            pass
        
        # Option 3: Auto-generate from dependencies and commands
        base_image = docker_config.get("base_image", "python:3.11-slim")
        apt_packages = docker_config.get("apt_packages", [])
        pip_packages = docker_config.get("pip_packages", [])
        run_commands = docker_config.get("run_commands", [])
        
        # Multi-stage build support
        final_base = docker_config.get("final_base")
        final_run_commands = docker_config.get("final_run_commands", [])
        
        dockerfile = f"FROM {base_image} as builder\n\n"
        
        # Add apt packages
        if apt_packages:
            dockerfile += "RUN apt-get update && apt-get install -y \\\n"
            for pkg in apt_packages:
                dockerfile += f"    {pkg} \\\n"
            dockerfile += "    && rm -rf /var/lib/apt/lists/*\n\n"
        
        # Add run commands
        if run_commands:
            for cmd in run_commands:
                dockerfile += f"RUN {cmd}\n"
            dockerfile += "\n"
            
        # Add pip packages
        if pip_packages:
            dockerfile += "RUN pip install --no-cache-dir"
            for pkg in pip_packages:
                dockerfile += f" {pkg}"
            dockerfile += "\n\n"
        
        # Handle final stage
        if final_base:
            dockerfile += f"FROM {final_base}\n\n"
            # Ensure python availability
            if "python" not in final_base.lower() and "alpine" in final_base.lower():
                dockerfile += "RUN apk add --no-cache python3 py3-pip\n\n"
            elif "python" not in final_base.lower() and ("debian" in final_base.lower() or "ubuntu" in final_base.lower() or "slim" in final_base.lower()):
                dockerfile += "RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*\n\n"
            
            if final_run_commands:
                for cmd in final_run_commands:
                    dockerfile += f"RUN {cmd}\n"
                dockerfile += "\n"
                
            # Copy from builder
            copy_config = docker_config.get("copy_from_builder", [])
            if copy_config:
                for item in copy_config:
                    if isinstance(item, str):
                        dockerfile += f"COPY --from=builder {item} {item}\n"
                    elif isinstance(item, dict) and "src" in item and "dest" in item:
                        dockerfile += f"COPY --from=builder {item['src']} {item['dest']}\n"
            
            elif "go install" in str(run_commands):
                dockerfile += "COPY --from=builder /go/bin/ /usr/local/bin/\n"
            else:
                dockerfile += "COPY --from=builder /usr/local/ /usr/local/\n"
        else:
            if "python" not in base_image.lower() and "alpine" in base_image.lower():
                dockerfile += "RUN apk add --no-cache python3 py3-pip\n\n"
        
        # Standard setup
        dockerfile += "WORKDIR /app\n"
        dockerfile += "ENV PYTHONUNBUFFERED=1\n"
        
        return dockerfile

    def build_tool_image(self, tool_name: str, docker_config: Dict, job_id: str) -> Tuple[bool, str, str]:
        """
        Builds the Docker image for a specific tool.
        Returns: (success, image_tag, logs)
        """
        logs = []
        def log(msg, level="info"):
            logs.append(msg)
            if level == "error":
                logger.error(msg, extra={"extra_fields": {"job_id": job_id, "tool_name": tool_name}})
            else:
                logger.info(msg, extra={"extra_fields": {"job_id": job_id, "tool_name": tool_name}})

        # Use authoritative tag generation
        image_tag = docker_config.get("image")
        
        # If no explicit override, generate authoritative tag
        if not image_tag or "security-platform-tool-" in image_tag:
             image_tag = utils.generate_image_tag(tool_name)
        
        log(f"🔨 Starting build for {tool_name} -> {image_tag}")
        
        # Prepare build context
        tool_build_dir = self.build_root_dir / f"tool-{tool_name}-{job_id}"
        if tool_build_dir.exists():
            shutil.rmtree(tool_build_dir)
        tool_build_dir.mkdir(parents=True)
        
        try:
            # Generate Dockerfile
            dockerfile_content = self.generate_dockerfile(tool_name, docker_config, tool_build_dir)
            if not dockerfile_content:
                # If no content returned, maybe it's using a pre-existing image without build config?
                # But if we are here, we probably wanted to build.
                # If "image" was set and no build config, we just assume it's valid.
                 if "image" in docker_config:
                     log(f"⏭️  Using pre-existing image: {image_tag}")
                     return True, image_tag, "\n".join(logs)
                 else:
                     return False, "", "❌ Could not generate Dockerfile configuration"
            
            dockerfile_path = tool_build_dir / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)
            
            # Execute Docker Build
            cmd = [
                "docker", "build",
                "-t", image_tag,
                "-f", str(dockerfile_path),
                str(tool_build_dir)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                log(line.strip())
                
            process.wait()
            
            if process.returncode == 0:
                log(f"✅ Successfully built {image_tag}")
                
                # Auto-load into k8s if configured (simulating the script logic)
                # But usually RegistryAdapter handles this. 
                # The previous script did it inline. 
                # For separation of concerns, we might let RegistryAdapter handle "load/push".
                # BUT, if we want full parity with the script which did "minikube image load":
                if os.getenv("AUTO_LOAD_K8S", "false").lower() == "true":
                     # We can call RegistryAdapter logic here or just do the simple minikube load
                     # Let's keep it simple and clean, RegistryAdapter is better suited for this.
                     pass
                
                return True, image_tag, "\n".join(logs)
            else:
                log(f"❌ Build failed with exit code {process.returncode}")
                return False, image_tag, "\n".join(logs)
                
        except Exception as e:
            log(f"💥 Exception during build: {e}")
            return False, image_tag, "\n".join(logs)
        finally:
            # Cleanup
            if tool_build_dir.exists():
                shutil.rmtree(tool_build_dir)
