import subprocess
import os
import sys
import json
import re

def run_vulnx(
    target: str = None,
    dorks: str = None,
    output_dir: str = None,
    number_pages: int = None,
    dork_list: str = None,
    ports: str = None,
    exploit: bool = False,
    cms_info: bool = False,
    web_info: bool = False,
    domain_info: bool = False,
    dns_info: bool = False
):
    """
    Run VulnX CMS Vulnerability Scanner.
    
    Args:
        target: URL target to scan (-u)
        dorks: Search webs with dorks (-D)
        output_dir: Specify output directory (-o) - Note: In Windmill context, usually captured via stdout
        number_pages: Search dorks number page limit (-n)
        dork_list: List names of dorks exploits (-l) [wordpress, prestashop, joomla, lokomedia, drupal, all]
        ports: Ports to scan (-p)
        exploit: Searching vulnerability & run exploits (-e)
        cms_info: Search cms info (--cms)
        web_info: Web informations gathering (-w)
        domain_info: Subdomains informations gathering (-d)
        dns_info: DNS informations gatherings (--dns)
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_vulnx")

    # Build argument list
    cmd_args = []
    
    if target:
        target = target.strip()
        if not target.startswith("http"):
            target = "http://" + target
        cmd_args.append(f"-u {target}")
    
    if dorks:
        cmd_args.append(f"-D '{dorks}'")
        
    if output_dir:
        cmd_args.append(f"-o {output_dir}")
        
    if number_pages:
        cmd_args.append(f"-n {number_pages}")
        
    if dork_list:
        cmd_args.append(f"-l {dork_list}")
        
    if ports:
        cmd_args.append(f"-p {ports}")
        
    if exploit:
        cmd_args.append("-e")
        
    if cms_info:
        cmd_args.append("--cms")
        
    if web_info:
        cmd_args.append("-w")

    if domain_info:
        cmd_args.append("-d")
        
    if dns_info:
        cmd_args.append("--dns")

    if not cmd_args:
        return {"error": "No arguments provided. Please provide a target (-u) or dorks (-D)."}

    args_str = " ".join(cmd_args)

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Construct command
    # Git clone + Install deps + Run
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/anouarbensaad/vulnx.git /vulnx >/dev/null 2>&1 && "
        "cd /vulnx && "
        "pip install -r requirements.txt >/dev/null 2>&1 && "
        f"python vulnx.py {args_str}"
    )
    
    cmd = [
        "docker", "run",
        "--rm",
        "--name", job_id,
        "--dns", "8.8.8.8",
        image,
        "sh", "-c",
        setup_and_run
    ]
    
    print(f"DEBUG: Running command: docker run ... vulnx {args_str}", file=sys.stderr, flush=True)
    
    try:
        # Use Popen to stream output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        results = []
        
        # Regex to capture useful info
        # VulnX output examples:
        # [+] Target : http://example.com
        # [+] CMS : WordPress
        # [+] Plugin : ...
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if line:
                    # Print raw line to stderr for realtime feedback (keeps colors in Windmill logs)
                    print(f"VULNX: {line}", file=sys.stderr, flush=True)
                    
                    # Strip ANSI codes for parsing
                    clean_line = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', line)
                    
                    if clean_line.startswith("[+]") or clean_line.startswith("[-]"):
                        parts = clean_line.split(":", 1)
                        if len(parts) == 2:
                            key = parts[0].replace("[+]", "").replace("[-]", "").strip()
                            value = parts[1].strip()
                            results.append({"key": key, "value": value})
        
        process.wait()

        if process.returncode != 0:
             stderr_output = process.stderr.read()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             # Don't fail immediately on non-zero, as some tools emit non-zero on minor issues but still give output
             if not results and stderr_output: # Only fail if no findings AND error
                 return {"error": "VulnX failed", "details": stderr_output}
        
        output = {"target": target if target else "Dorks/Multiple", "findings": results}
        if dorks:
            output["dorks"] = dorks
            
        return output

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "http://testphp.vulnweb.com", cms_info: bool = True):
    print(f"DEBUG: Scanning target: {target} with cms_info={cms_info}", file=sys.stderr, flush=True)
    result = run_vulnx(target=target, cms_info=cms_info)
    print(json.dumps(result, indent=2), flush=True)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Simple test arg parsing
        target_arg = sys.argv[1]
        main(target_arg)
    else:
        main()
