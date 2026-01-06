import re

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

def generate_image_tag(tool_identifier: str) -> str:
    """
    Generate authoritative Docker image tag from tool identifier.
    Extracts slug if path (e.g. 'Network/nmap_scan' -> 'nmap_scan')
    Sanitizes slug (e.g. 'nmap_scan' -> 'nmap-scan')
    Returns: security-platform-tool-nmap-scan:latest
    """
    if not tool_identifier:
        return "security-platform-tool-unknown:latest"
        
    # Extract slug if path
    slug = tool_identifier
    if '/' in tool_identifier:
        slug = tool_identifier.split('/')[-1]
        
    safe_slug = sanitize_k8s_name(slug)
    return f"security-platform-tool-{safe_slug}:latest"
