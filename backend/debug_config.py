import os
from config import settings
from core import utils

def debug_env():
    print(f"--- Environment Variables ---")
    print(f"DOCKER_REGISTRY in os.environ: '{os.environ.get('DOCKER_REGISTRY')}'")
    print(f"DOCKER_REGISTRY_PUSH in os.environ: '{os.environ.get('DOCKER_REGISTRY_PUSH')}'")
    
    print(f"\n--- Settings Object ---")
    print(f"settings.DOCKER_REGISTRY: '{settings.DOCKER_REGISTRY}'")
    print(f"settings.DOCKER_REGISTRY_PUSH: '{settings.DOCKER_REGISTRY_PUSH}'")
    
    print(f"\n--- Utils Generation ---")
    print(f"get_docker_registry(): '{utils.get_docker_registry()}'")
    print(f"generate_image_tag('test'): '{utils.generate_image_tag('test')}'")

if __name__ == "__main__":
    debug_env()
