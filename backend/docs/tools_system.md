# 🛠️ Sistema de Ferramentas (Tools System)

O ContextWorks trata as ferramentas como cidadãos de primeira classe. Uma ferramenta é definida pela combinação de Código (Python) e Metadados (YAML).

## Anatomia de uma Ferramenta

No diretório `backend/tools/`, cada ferramenta deve ter:

### 1. Script Python (`minha_tool.py`)
Deve ser um script autocontido que aceita argumentos via linha de comando ou variáveis de ambiente.

```python
import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    
    # Lógica da ferramenta...
    result = {"status": "scanned", "target": args.url}
    
    # Saída deve ser em JSON (preferencialmente)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### 2. Definição YAML (`minha_tool.yaml`)
Define como o ContextWorks deve interagir com a ferramenta.

```yaml
name: "Web Scanner"
description: "Scans a website for vulnerabilities."
version: "1.0.0"
docker:
  image: "contextworks/scanner-web:v1"  # Imagem que será usada no Job
args:
  - name: "url"
    type: "string"
    description: "Target URL to scan"
    required: true
resources:
  cpu: "500m"
  memory: "256Mi"
```

## Processo de Sincronização (Scan)

O backend possui um endpoint de "Sync" ou "Scan" que:
1. Percorre recursivamente o diretório de ferramentas (ou baixa do banco de dados).
2. Lê os arquivos `.yaml`.
3. Atualiza ou Cria o registro na tabela `tools` do PostgreSQL.
4. Garante que a versão no banco bata com a versão do arquivo.

Esta abordagem "Infrastructure as Code" permite versionar suas ferramentas no Git junto com o código da plataforma.
