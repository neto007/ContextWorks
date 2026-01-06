import json
from typing import Dict, Any
from kubernetes import client
from config import settings
from core.logger import logger
from .resolver import get_tool_config_from_data

K8S_NAMESPACE = settings.K8S_NAMESPACE

def create_k8s_job(tool_data: Dict[str, Any], args: Dict[str, Any], job_name: str, job_id: str):
    """
    Creates the K8s Job object using data from DB.
    """
    script_content = tool_data.get('script_code', '')
    if not script_content:
         raise ValueError(f"Tool {tool_data.get('name')} has no script code")

    # Detect tool configuration (image and resources)
    tool_config = get_tool_config_from_data(tool_data)
    tool_image = tool_config["image"]
    tool_resources = tool_config["resources"]

    wrapper_code = """
import sys, json, importlib.util, os, inspect

script_content = sys.argv[1]
args = json.loads(sys.argv[2])

os.makedirs("/app", exist_ok=True)
with open("/app/tool.py", "w") as f:
    f.write(script_content)

try:
    spec = importlib.util.spec_from_file_location("tool_module", "/app/tool.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "main"):
        sig = inspect.signature(module.main)
        params = list(sig.parameters.values())
        num_params = len(params)
        
        if num_params == 0:
            ans = module.main()
        elif num_params == 1:
            param = params[0]
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                 ans = module.main(**args)
            elif param.name == 'args':
                 ans = module.main(args)
            else:
                 try:
                     ans = module.main(**args)
                 except TypeError:
                     ans = module.main(args)
        else:
            ans = module.main(**args)
            
        if ans is not None:
            print("\\n--- RESULT ---")
            if isinstance(ans, (dict, list)):
                print(json.dumps(ans, indent=2))
            else:
                print(str(ans))
    else:
        print("Error: No main function found")
        sys.exit(1)
except Exception as e:
    print(f"Error executing script: {e}")
    sys.exit(1)
"""

    batch_v1 = client.BatchV1Api()
    
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(
            name=job_name,
            labels={
                "app": "security-platform-tool",
                "execution-id": job_id
            }
        ),
        spec=client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"job-name": job_name}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="executor",
                            image=tool_image,
                            image_pull_policy="IfNotPresent",
                            command=["python3", "-c", wrapper_code, script_content, json.dumps(args)],
                            env=[client.V1EnvVar(name="PYTHONUNBUFFERED", value="1")],
                            resources=client.V1ResourceRequirements(
                                requests=tool_resources["requests"],
                                limits=tool_resources["limits"]
                            )
                        )
                    ],
                    restart_policy="Never"
                )
            ),
            backoff_limit=0,
            ttl_seconds_after_finished=600
        )
    )
    
    logger.info("Submitting K8s Job", extra={"extra_fields": {"job_name": job_name, "namespace": K8S_NAMESPACE, "image": tool_image, "execution_id": job_id}})
    try:
        batch_v1.create_namespaced_job(namespace=K8S_NAMESPACE, body=job)
        logger.info("K8s Job created successfully", extra={"extra_fields": {"job_name": job_name}})
    except Exception as e:
        logger.error("Failed to create K8s Job", exc_info=True, extra={"extra_fields": {"job_name": job_name, "namespace": K8S_NAMESPACE}})
        raise

def delete_k8s_job(job_name: str):
    batch_v1 = client.BatchV1Api()
    try:
        batch_v1.delete_namespaced_job(
            name=job_name,
            namespace=K8S_NAMESPACE,
            propagation_policy='Foreground'
        )
    except:
        pass

def parse_result_from_logs(logs: str) -> Any:
    lines = logs.strip().split('\n')
    if lines:
        last_line = lines[-1]
        try:
            return json.loads(last_line)
        except:
            return last_line
    return None
