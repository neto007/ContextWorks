# 🔌 Referência de API

Esta página documenta os principais endpoints da API RESTful do ContextWorks.

> **Nota**: A documentação interativa completa (Swagger/OpenAPI) está disponível em `/docs` quando o servidor está rodando.

## Autenticação

Todos os endpoints protegidos exigem o header:
`Authorization: Bearer <seu_token_jwt>`

### Login (`POST /auth/login`)
Troca credenciais (username/password) por um Access Token.

**Body:**
```json
{
  "username": "admin@contextworks.com",
  "password": "secret_password"
}
```

## Ferramentas (Tools)

### Listar Ferramentas (`GET /tools`)
Retorna todas as ferramentas disponíveis no workspace.

**Parâmetros:**
- `workspace` (query, opcional): Filtrar por workspace específico.

### Executar Ferramenta (`POST /tools/{id}/execute`)
Neste endpoint, a mágica acontece. O backend cria um Job no Kubernetes.

**Body:**
```json
{
  "args": {
    "url": "https://example.com",
    "port": 8080
  }
}
```

**Response:**
```json
{
  "job_id": "job-12345-abcde",
  "status": "pending",
  "stream_url": "/execution/job-12345-abcde/stream"
}
```

## Logs & Streaming

### Stream de Logs (`GET /execution/{job_id}/stream`)
Endpoint SSE (Server-Sent Events) que retorna os logs em tempo real do Pod de execução.

**Formato de Evento:**
```text
data: {"timestamp": "2024-01-01T12:00:00Z", "message": "Starting scan..."}
```

## Protocolo MCP

### Servidor MCP (`/mcp`)
Endpoint compatível com o **Model Context Protocol**. Permite que LLMs (como Claude ou GPT-4) descubram e utilizem as ferramentas do ContextWorks.

- **GET /mcp/tools**: Lista ferramentas no formato MCP.
- **POST /mcp/call**: Executa uma ferramenta via protocolo MCP.
