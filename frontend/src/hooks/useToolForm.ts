import { useState, useEffect, useCallback } from 'react';
import type { Argument, DockerMode } from '../types/tool';
import { validatePythonCode } from '../lib/python-validator';
import type { ValidationResult } from '../lib/python-validator';
import { toolService } from '../services/toolService';
import { useToast } from '../components/Toast';

export const TEMPLATES = {
    basic: {
        name: 'Basic Script',
        code: `#!/usr/bin/env python3
import sys
import json

def main(args):
    result = {"status": "success", "data": {}}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    main(args)
`,
        arguments: [] as Argument[]
    },
    network_scanner: {
        name: 'Network Scanner',
        code: `#!/usr/bin/env python3
import sys
import json
import socket

def scan_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main(args):
    host = args.get('target', 'localhost')
    ports = args.get('ports', '80,443').split(',')
    
    open_ports = []
    for port in ports:
        if scan_port(host, int(port)):
            open_ports.append(int(port))
    
    result = {
        "status": "success",
        "target": host,
        "open_ports": open_ports,
        "total_scanned": len(ports)
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    main(args)
`,
        arguments: [
            { name: 'target', type: 'str' as const, description: 'Target host', required: true },
            { name: 'ports', type: 'str' as const, description: 'Ports to scan (comma-separated)', required: false, default: '80,443' }
        ]
    },
    web_scanner: {
        name: 'Web Vulnerability Scanner',
        code: `#!/usr/bin/env python3
import sys
import json
import requests

def scan_web(url):
    vulnerabilities = []
    
    try:
        response = requests.get(url, timeout=5)
        
        if 'X-Frame-Options' not in response.headers:
            vulnerabilities.append("Missing X-Frame-Options header")
        
        if 'X-Content-Type-Options' not in response.headers:
            vulnerabilities.append("Missing X-Content-Type-Options header")
            
        if 'Strict-Transport-Security' not in response.headers and url.startswith('https'):
            vulnerabilities.append("Missing HSTS header")
        
        return {
            "status": "success",
            "url": url,
            "vulnerabilities": vulnerabilities,
            "status_code": response.status_code
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main(args):
    url = args.get('url', '')
    if not url:
        print(json.dumps({"status": "error", "message": "URL required"}, indent=2))
        return
    
    result = scan_web(url)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    main(args)
`,
        arguments: [
            { name: 'url', type: 'str' as const, description: 'Target URL to scan', required: true }
        ]
    }
};

export const useToolForm = (initialData?: any) => {
    const [toolName, setToolName] = useState(initialData?.name || '');
    const [description, setDescription] = useState(initialData?.description || '');
    const [scriptCode, setScriptCode] = useState(initialData?.script_code || TEMPLATES.basic.code);
    const [arguments_, setArguments] = useState<Argument[]>(initialData?.arguments || []);
    const [selectedTemplate, setSelectedTemplate] = useState<keyof typeof TEMPLATES>('basic');
    const [submitting, setSubmitting] = useState(false);
    const [loading, setLoading] = useState(false);
    const [validation, setValidation] = useState<ValidationResult>({ valid: true, errors: [], warnings: [] });
    const [logoSVG, setLogoSVG] = useState<string | null>(initialData?.has_logo ? 'loading' : null);

    // Docker & Resources configuration
    const [dockerMode, setDockerMode] = useState<DockerMode>('auto');
    const [preexistingImage, setPreexistingImage] = useState('');
    const [baseImage, setBaseImage] = useState('python:3.11-slim');
    const [aptPackages, setAptPackages] = useState<string[]>([]);
    const [pipPackages, setPipPackages] = useState<string[]>([]);
    const [cpuRequest, setCpuRequest] = useState('100m');
    const [cpuLimit, setCpuLimit] = useState('1000m');
    const [memoryRequest, setMemoryRequest] = useState('256Mi');
    const [memoryLimit, setMemoryLimit] = useState('1024Mi');

    const toast = useToast();

    // Validate code whenever it changes
    useEffect(() => {
        const result = validatePythonCode(scriptCode);
        setValidation(result);
    }, [scriptCode]);

    const populateFromTool = useCallback((data: any) => {
        setToolName(data.name || '');
        setDescription(data.description || '');
        setScriptCode(data.script_code || '');
        setArguments(data.arguments || []);

        if (data.docker) {
            setDockerMode(data.docker.docker_mode || 'auto');
            setPreexistingImage(data.docker.image || '');
            setBaseImage(data.docker.base_image || 'python:3.11-slim');
            setAptPackages(data.docker.apt_packages || []);
            setPipPackages(data.docker.pip_packages || []);

            const res = data.docker.resources || data.resources;
            if (res) {
                if (res.requests) {
                    setCpuRequest(res.requests.cpu || '100m');
                    setMemoryRequest(res.requests.memory || '256Mi');
                }
                if (res.limits) {
                    setCpuLimit(res.limits.cpu || '1000m');
                    setMemoryLimit(res.limits.memory || '1024Mi');
                }
            }
        } else if (data.resources) {
            const res = data.resources;
            if (res.requests) {
                setCpuRequest(res.requests.cpu || '100m');
                setMemoryRequest(res.requests.memory || '256Mi');
            }
            if (res.limits) {
                setCpuLimit(res.limits.cpu || '1000m');
                setMemoryLimit(res.limits.memory || '1024Mi');
            }
        }
    }, []);

    const handleTemplateChange = useCallback((template: keyof typeof TEMPLATES) => {
        setSelectedTemplate(template);
        setScriptCode(TEMPLATES[template].code);
        setArguments(TEMPLATES[template].arguments);
    }, []);

    const submitTool = useCallback(async (workspace: string, editId?: string) => {
        if (!toolName.trim()) {
            toast.error('Tool name is required');
            return null;
        }

        setSubmitting(true);
        try {
            const toolData = {
                category: workspace,
                name: toolName,
                description: description || `Security tool: ${toolName}`,
                script_code: scriptCode,
                arguments: arguments_,
                docker: {
                    docker_mode: dockerMode,
                    image: dockerMode === 'preexisting' ? preexistingImage : undefined,
                    base_image: (dockerMode === 'auto' || dockerMode === 'custom') ? baseImage : undefined,
                    apt_packages: aptPackages.length > 0 ? aptPackages : undefined,
                    pip_packages: pipPackages.length > 0 ? pipPackages : undefined,
                    resources: dockerMode !== 'auto' ? {
                        requests: { cpu: cpuRequest, memory: memoryRequest },
                        limits: { cpu: cpuLimit, memory: memoryLimit }
                    } : undefined
                }
            };

            let response;
            if (editId) {
                const parts = editId.split('/');
                const cat = parts.length > 1 ? parts[0] : workspace;
                const id = parts.length > 1 ? parts[1] : editId;
                response = await toolService.updateTool(cat, id, toolData);
            } else {
                response = await toolService.createTool(toolData);
            }

            // Upload logo if provided and changed
            if (logoSVG && logoSVG !== 'loading') {
                const toolIdForResult = editId || (response as any).id || (response as any).tool?.id || toolName;
                const cleanToolId = toolIdForResult.includes('/') ? toolIdForResult.split('/').pop() : toolIdForResult;
                const parts = (editId || "").split('/');
                const cat = parts.length > 1 ? parts[0] : workspace;
                await toolService.uploadLogo(cat, cleanToolId!, logoSVG);
            }

            return response;
        } catch (err: any) {
            toast.error(err.message || 'Failed to save tool');
            return null;
        } finally {
            setSubmitting(false);
        }
    }, [toolName, description, scriptCode, arguments_, dockerMode, preexistingImage, baseImage, aptPackages, pipPackages, cpuRequest, memoryRequest, cpuLimit, memoryLimit, logoSVG, toast]);

    return {
        toolName, setToolName,
        description, setDescription,
        scriptCode, setScriptCode,
        arguments_, setArguments,
        selectedTemplate, setSelectedTemplate,
        submitting, loading, setLoading,
        validation,
        logoSVG, setLogoSVG,
        dockerMode, setDockerMode,
        preexistingImage, setPreexistingImage,
        baseImage, setBaseImage,
        aptPackages, setAptPackages,
        pipPackages, setPipPackages,
        cpuRequest, setCpuRequest,
        cpuLimit, setCpuLimit,
        memoryRequest, setMemoryRequest,
        memoryLimit, setMemoryLimit,
        handleTemplateChange,
        populateFromTool,
        submitTool
    };
};
