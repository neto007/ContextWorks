import subprocess
import os
import sys
import json
import re

def run_garak(
    model_type: str = "openai",
    model_name: str = "gpt-3.5-turbo",
    api_key: str = "",
    probes: str = "encoding",
    generations: int = None
):
    """
    Run garak LLM Vulnerability Scanner.
    
    Args:
        model_type: Model type (huggingface, openai, replicate, cohere, ggml, etc.)
        model_name: Model name (e.g. gpt-3.5-turbo, meta-llama/Llama-2-7b-chat-hf)
        api_key: API Key for the provider (OPENAI_API_KEY, HUGGINGFACE_API_KEY, etc.)
        probes: Probes to run (comma separated, e.g. encoding,misleading). Default: encoding (fast)
        generations: Number of generations per prompt (default 10 in garak)
    """
    image = "python:3.10-slim"
    job_id = os.environ.get("WM_JOB_ID", "local_test_garak")

    # Command construction
    cmd_args = [
        "--model_type", model_type,
        "--model_name", model_name,
        "--probes", probes
    ]
    
    if generations:
        cmd_args.extend(["--generations", str(generations)])

    args_str = " ".join(cmd_args)
    
    # Environment variables for the container
    env_vars = {}
    
    # Map generic api_key to specific env vars based on model_type
    key_map = {
        "openai": "OPENAI_API_KEY",
        "huggingface": "HF_TOKEN",
        "replicate": "REPLICATE_API_TOKEN",
        "cohere": "COHERE_API_KEY"
    }
    
    # Safe default if type not in map, just don't set invalid env or let user handle upstream
    env_var_name = key_map.get(model_type.lower())
    dock_env_args = []
    
    if env_var_name and api_key:
         # We pass this via env to docker run
         # BUT for simpler "on-the-fly" execution inside 'sh -c', getting envs in is tricky if we don't want to print them in 'ps'.
         # Windmill secrets are safe.
         # We will write the command such that it exports the env before running.
         pass
    
    # Installation command
    # Install git explicitly just in case.
    # We remove >/dev/null to debug installation.
    setup_and_run = (
        "python3 -m pip install -U garak && "
        f"{env_var_name}='{api_key}' " if env_var_name and api_key else ""
        "python3 -m garak " + args_str
    )
    
    # If using test/dry-run without API key, garak might fail or we connect to test dummy?
    # Garak has a 'test' probe.
    
    cmd = [
        "docker", "run",
        "--rm",
        "--name", job_id,
        image,
        "sh", "-c",
        setup_and_run
    ]
    
    print(f"DEBUG: Running garak {args_str}", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        results = []
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if line:
                    print(f"GARAK: {line}", file=sys.stderr, flush=True)
                    # Parsing garak output is tricky as it's verbose.
                    # We look for "scoring" or "failure" lines.
                    if "failure" in line.lower() and "%" in line:
                         results.append(line)

        process.wait()

        if process.returncode != 0:
             stderr_output = process.stderr.read()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             # If it fails due to missing API key (common in test), return error
             if "API key" in stderr_output or "Environment variable" in stderr_output:
                 return {"error": "Missing or Invalid API Key", "details": stderr_output}
             if not results:
                 return {"error": "Garak execution failed", "details": stderr_output}

        return {
            "model_type": model_type,
            "model_name": model_name,
            "findings": results if results else "No obvious vulnerabilities found (or parsing missed them). check logs."
        }

    except Exception as e:
        return {"error": str(e)}

def main(model_type="test", model_name="test"):
    # Garak doesn't have a simple 'test' mode that requires NO api key easily accessible...
    # Actually 'test.Test' probe works on 'test.Test' generator?
    # Let's try to run a --list_probes command for verification if full scan fails.
    pass

    # For the real main:
    print(json.dumps(run_garak(model_type, model_name), indent=2), flush=True)

if __name__ == "__main__":
    # Windmill entrypoint
    # We will just run default if called directly
    if len(sys.argv) > 1:
        # minimal arg parsing for testing
        pass
    else:
        # Mock for verification step: run --help or similar if verify mode
        # User defined test:
        run_garak(model_type="test", model_name="test")
