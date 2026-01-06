#!/usr/bin/env python3
"""
Nmap Scan Tool
Executes Nmap network scans with advanced configuration options and structured XML parsing..
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import tempfile
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

def main(**args):
    """
    Execute Nmap scan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for nmap
    nmap_path = shutil.which("nmap")
    if not nmap_path:
        # Fallback path check
        if os.path.exists("/usr/bin/nmap"):
            nmap_path = "/usr/bin/nmap"
        elif os.path.exists("/usr/local/bin/nmap"):
            nmap_path = "/usr/local/bin/nmap"
        else:
            return {"status": "error", "message": f"nmap binary not found. PATH={os.environ.get('PATH')}"}

    # Sanitize target (remove protocol)
    if "://" in target:
        try:
            parsed = urlparse(target)
            target = parsed.netloc
        except Exception:
            pass  # fallback to original if parsing fails

    # Remove trailing slash if present
    target = target.rstrip("/")

    # Base command
    # -oX - : Output XML to stdout
    command = [nmap_path, target, "-oX", "-"]

    # Port specification
    port_spec = args.get('port_spec')
    if port_spec:
        command.extend(["-p", port_spec])

    # Scan Type
    scan_type = args.get('scan_type', 'connect')
    if scan_type == 'syn':
        command.append('-sS')
    elif scan_type == 'connect':
        command.append('-sT')
    elif scan_type == 'udp':
        command.append('-sU')
    elif scan_type == 'version':
        command.append('-sV')
    elif scan_type == 'comprehensive':
        command.extend(['-sS', '-sU', '-sV', '-O'])

    # Timing
    timing = args.get('timing', 'T3')
    if timing in ["T0", "T1", "T2", "T3", "T4", "T5"]:
        command.append(f'-{timing}')

    # Aggressive
    if args.get('aggressive'):
        command.append('-A')

    # Service Detection
    if args.get('service_detection') and '-sV' not in command and '-A' not in command:
        command.append('-sV')

    # OS Detection
    if args.get('os_detection') and '-O' not in command and '-A' not in command:
        command.append('-O')

    # Scripts
    scripts = args.get('scripts')
    if scripts:
        command.extend(['--script', scripts])

    # Extra arguments
    # Output format
    # Use a temporary file for XML output so we can stream verbose output to stdout
    
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp_xml:
        xml_output_path = tmp_xml.name
    
    command.extend(["-oX", xml_output_path])
    
    # Add verbose flag to get real-time progress in stdout
    if "-v" not in command:
        command.append("-v")
        
    # Stats every 5s for responsiveness
    command.extend(["--stats-every", "5s"])

    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        # Popen to stream output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=sys.stderr, # Send stderr directly to system stderr (logs)
            text=True,
            bufsize=1
        )
        
        # Stream stdout (human readable progress) to stderr for the platform to pick up as logs
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"NMAP: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        # Parse XML Output from file
        scan_data = {
            "target": target,
            "hosts": []
        }
        
        parse_error = None

        try:
            tree = ET.parse(xml_output_path)
            root = tree.getroot()
                
            for host in root.findall('host'):
                host_data = {
                    "address": "",
                    "hostnames": [],
                    "ports": [],
                    "os_match": []
                }
                
                # Address
                address = host.find('address')
                if address is not None:
                    host_data["address"] = address.get('addr')
                    
                # Hostnames
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    for hn in hostnames.findall('hostname'):
                        host_data["hostnames"].append(hn.get('name'))

                # Ports
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        port_data = {
                            "port": int(port.get('portid')),
                            "protocol": port.get('protocol'),
                            "state": port.find('state').get('state') if port.find('state') is not None else "unknown",
                            "service": "unknown",
                            "reason": port.find('state').get('reason') if port.find('state') is not None else ""
                        }
                        
                        service = port.find('service')
                        if service is not None:
                            port_data["service"] = service.get('name', 'unknown')
                            product = service.get('product')
                            version = service.get('version')
                            if product:
                                port_data["product"] = product
                            if version:
                                port_data["version"] = version
                                
                        host_data["ports"].append(port_data)

                # OS Match (if available)
                os_matches = host.find('os')
                if os_matches is not None:
                    for os_match in os_matches.findall('osmatch'):
                        host_data["os_match"].append({
                            "name": os_match.get('name'),
                            "accuracy": os_match.get('accuracy')
                        })

                scan_data["hosts"].append(host_data)
                
        except ET.ParseError as e:
            parse_error = str(e)
            if status == "success":
                 status = "partial_error"
                 scan_data["parse_error"] = f"Scan ran but failed to parse XML: {str(e)}"
        
        # Clean up
        if os.path.exists(xml_output_path):
            os.remove(xml_output_path)

        # Construct summary
        host_count = len(scan_data["hosts"])
        total_open_ports = sum(
            len([p for p in h["ports"] if p.get("state") == "open"]) 
            for h in scan_data["hosts"]
        )
        summary = f"Scan complete. Found {host_count} hosts and {total_open_ports} open ports."
        
        output_data = {
            "status": status,
            "message": summary,
            "data": scan_data
        }
        
        if parse_error:
            output_data["data"]["parse_error_details"] = parse_error

        return output_data

    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'xml_output_path' in locals() and os.path.exists(xml_output_path):
             os.remove(xml_output_path)
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            # If valid JSON not provided, maybe arguments passed as --key value ?
            # For simplicity, we stick to JSON input or just default
            params = {}
    
    print(json.dumps(main(**params), indent=2))
