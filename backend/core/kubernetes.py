"""
Kubernetes client setup and utilities
"""
from kubernetes import client, config as k8s_config
from core.logger import logger

# Global K8s client
_k8s_configured = False

def setup_kubernetes():
    """Initialize Kubernetes client configuration"""
    global _k8s_configured
    
    if _k8s_configured:
        return
    
    try:
        k8s_config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config")
    except k8s_config.ConfigException:
        try:
            k8s_config.load_kube_config()
            logger.info("Loaded local kube config")
        except Exception as e:
            logger.error("Error loading Kubernetes configuration", exc_info=True)
    
    _k8s_configured = True

def get_batch_client() -> client.BatchV1Api:
    """Get Kubernetes Batch API client"""
    setup_kubernetes()
    return client.BatchV1Api()

def get_core_client() -> client.CoreV1Api:
    """Get Kubernetes Core API client"""
    setup_kubernetes()
    return client.CoreV1Api()
