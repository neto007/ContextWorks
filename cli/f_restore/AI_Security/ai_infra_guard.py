import subprocess
import os
import sys
import json

def run_ai_infra_guard(target: str = ""):
    """
    Run AI-Infra-Guard (AI Infrastructure Scanner).
    
    Args:
        target: Target IP/Host/URL to scan for AI infra vulnerabilities (CVEs in Ollama, ComfyUI, etc.)
    """
    # AI-Infra-Guard is a platform, but we focus on the core scanning capability.
    # It uses a Go-based scanner.
    
    image = "golang:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_ai_infra_guard")
    
    # We will clone and build the scanner component.
    # Based on the repo structure, we look for core/cmd/.. or similar.
    # Official docs suggest using it as a platform, but we can try to run the scan logic.
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/Tencent/AI-Infra-Guard.git /app >/dev/null 2>&1 && "
        "cd /app && "
        "go build -o aigard main.go >/dev/null 2>&1 && "
        f"./aigard scan --target {target}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running AI-Infra-Guard scan on {target}...", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        findings = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if line:
                    print(f"AI-INFRA-GUARD: {line}", file=sys.stderr, flush=True)
                    # Basic parsing: look for [VULN] or [CVE]
                    if "[VULN]" in line or "[CVE]" in line or "VulnFound" in line:
                         findings.append(line)
        
        process.wait()
        
        return {
            "target": target,
            "vulnerabilities": findings if findings else "No AI infrastructure vulnerabilities found."
        }
        
    except Exception as e:
        return {"error": str(e)}

def main(target: str = "127.0.0.1"):
    print(json.dumps(run_ai_infra_guard(target), indent=2), flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
