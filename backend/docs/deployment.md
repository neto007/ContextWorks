# 🚀 Deployment e Operações Kubernetes

O backend do ContextWorks foi desenhado para ser **Kubernetes-Native**. Isso significa que ele não apenas roda dentro do cluster, mas também conversa com a API do Kubernetes para criar recursos (Jobs).

## Pré-requisitos do Cluster

Para o backend funcionar corretamente, o cluster deve ter:
- **ServiceAccount** com permissões de `create`, `get`, `list`, `watch`, `delete` recursos do tipo `jobs` e `pods`.
- **Namespace** dedicado (padrão: `contextworks-platform`).
- **Secrets** configurados para acesso ao banco de dados e registry docker.

## Dockerfile e Build

O Build é feito em dois estágios para minimizar o tamanho da imagem final:

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim-bookworm as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN uv sync --frozen --no-install-project

# Stage 2: Runtime
FROM python:3.12-slim-bookworm
COPY --from=builder /app/.venv /app/.venv
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0"]
```

## Variáveis de Ambiente Críticas

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `DATABASE_URL` | String de conexão PostgreSQL (asyncpg) | `postgresql+asyncpg://user:pass@db:5432/db` |
| `K8S_NAMESPACE` | Namespace onde os Jobs serão criados | `contextworks-platform` |
| `JOB_IMAGE_PREFIX` | Prefixo da imagem Docker das ferramentas | `myregistry.com/tools/` |
| `SECRET_KEY` | Chave para assinatura JWT | `openssl rand -hex 32` |

## Ciclo de Vida do Pod de Execução

Quando um usuário pede para rodar uma ferramenta:

1. **Backend**: Recebe request POST `/tools/{id}/execute`.
2. **K8s API**: Cria um objeto `Job` com a imagem específica da ferramenta.
3. **Job**: Inicia, roda o script Python com os argumentos passados.
4. **Logs**: O backend conecta no stream de logs do Pod gerado pelo Job.
5. **Cleanup**: O Job é deletado automaticamente após sucesso (configurável via TTL) ou pelo Garbage Collector.
