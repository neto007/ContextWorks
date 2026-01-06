import subprocess
import os
import sys
import json
import tempfile
import base64

def run_tai_e(
    file_content: bytes = b"",
    filename: str = "app.jar"
):
    """
    Run Tai-e (Static Analysis Framework for Java).
    
    Args:
        file_content: Conteúdo do arquivo JAR/class (bytes ou base64 string).
                     No Windmill, você pode ler de S3: wmill.get_resource("u/user/my_jar")
        filename: Nome do arquivo (usado para extensão).
    """
    image = "openjdk:11-jre-slim"
    job_id = os.environ.get("WM_JOB_ID", "local_test_tai_e")
    
    # Se recebeu string base64, decodifica
    if isinstance(file_content, str):
        try:
            file_content = base64.b64decode(file_content)
        except:
            return {"error": "file_content deve ser bytes ou base64 string válida"}
    
    if not file_content:
        return {"error": "file_content não pode estar vazio"}
    
    # Cria arquivo temporário local
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, filename)
        
        # Escreve o conteúdo no arquivo temporário
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        print(f"DEBUG: Arquivo criado: {file_path} ({len(file_content)} bytes)", file=sys.stderr, flush=True)
        
        # Tai-e is a Java framework. We'll use a pre-built jar if possible or just show help.
        setup_and_run = (
            "apt-get update >/dev/null && apt-get install -y wget >/dev/null && "
            "wget https://github.com/pascal-lab/Tai-e/releases/latest/download/tai-e-all.jar -O /app/tai-e.jar >/dev/null 2>&1 && "
            f"java -jar /app/tai-e.jar -a /app_data/{filename}"
        )
        
        cmd = [
            "docker", "run", "--rm", "--name", job_id,
            "-v", f"{tmpdir}:/app_data",
            image, "sh", "-c", setup_and_run
        ]
        
        print(f"DEBUG: Running Tai-e on {filename}...", file=sys.stderr, flush=True)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {"error": str(e)}

def main(file_content: bytes = b"", filename: str = "test.jar"):
    """
    Exemplo de uso no Windmill:
    
    # Opção 1: Ler de S3 resource
    import wmill
    jar_content = wmill.get_resource("u/user/my_app_jar")
    result = run_tai_e(jar_content, "MyApp.jar")
    
    # Opção 2: Upload via UI (Windmill converte para bytes automaticamente)
    # Basta configurar o input como 'bytes' no YAML
    """
    if not file_content:
        return {"error": "Forneça file_content (bytes do arquivo JAR/class)"}
    
    print(json.dumps(run_tai_e(file_content, filename), indent=2), flush=True)

if __name__ == "__main__":
    main()
