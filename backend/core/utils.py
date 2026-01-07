import re
from config import settings
from core import database

def sanitize_k8s_name(name: str) -> str:
    """
    Sanitize name for Kubernetes (RFC 1123 compatible).
    Converts to lowercase, replaces invalid chars with dashes, removes consecutive dashes.
    """
    if not name:
        return "unnamed"
    safe = re.sub(r'[^a-z0-9]', '-', name.lower().replace('_', '-').replace(' ', '-'))
    safe = re.sub(r'-+', '-', safe)
    return safe.strip('-')

def get_docker_registry() -> str:
    """
    Get Docker registry from database config (set via frontend) or fallback to env settings.
    For local type, returns the internal cluster registry.
    """
    try:
        # Try to get from database (set via frontend)
        config = database.get_registry_config()
        if config:
            registry_type = config.get('type', 'local')
            
            if registry_type == 'local':
                # Local development - use internal cluster registry
                return settings.DOCKER_REGISTRY
            elif registry_type == 'dockerhub':
                # Docker Hub: namespace/image
                namespace = config.get('namespace', '')
                return namespace if namespace else 'library'
            elif registry_type in ['ecr', 'gcr']:
                # AWS ECR or GCR: full URL
                url = config.get('url', '')
                namespace = config.get('namespace', '')
                if url and namespace:
                    return f"{url}/{namespace}"
                elif url:
                    return url
        
    except Exception:
        # If database not available or error, use env fallback
        pass
    
    # Fallback to environment variable or default
    return settings.DOCKER_REGISTRY

def generate_image_tag(tool_identifier: str) -> str:
    """
    Generate authoritative Docker image tag from tool identifier.
    Extracts slug if path (e.g. 'Network/nmap_scan' -> 'nmap_scan')
    Sanitizes slug (e.g. 'nmap_scan' -> 'nmap-scan')
    Returns: {DOCKER_REGISTRY}/security-platform-tool-nmap-scan:latest
    
    Registry is determined by:
    1. Database config (set via frontend /settings page)
    2. DOCKER_REGISTRY environment variable
    3. Default: mcp-registry.security-platform.svc:5000
    """
    registry = get_docker_registry()
    
    if not tool_identifier:
        return f"{registry}/security-platform-tool-unknown:latest"
        
    # Extract slug if path
    slug = tool_identifier
    if '/' in tool_identifier:
        slug = tool_identifier.split('/')[-1]
        
    safe_slug = sanitize_k8s_name(slug)
    return f"{registry}/security-platform-tool-{safe_slug}:latest"
