# Documentação MCP - Server-Sent Events (SSE) + Mensagens

## Visão Geral

O **MCP (Model Context Protocol)** usa uma arquitetura híbrida para comunicação bidirecional:
- **SSE (Server-Sent Events)**: Servidor → Cliente (streaming unidirecional)
- **HTTP POST**: Cliente → Servidor (requisições JSON-RPC 2.0)

## Arquitetura de Comunicação

```
┌──────────────────────────────────────────────────────────┐
│                    CLIENTE MCP                            │
│  (ex: Claude Desktop, EvoAI, qualquer cliente MCP)       │
└───────────────┬──────────────────────────────────────────┘
                │
                │ ① GET /mcp/{id}/sse (mantém conexão aberta)
                ├────────────────────────────────────────▶
                │                                           
                │ ② event: endpoint                         
                │    data: /mcp/{id}/message                
                ◀────────────────────────────────────────┤
                │                                           │
                │ ③ POST /mcp/{id}/message                  │
                │    {JSON-RPC request}                     │
                ├────────────────────────────────────────▶ │
                │                                           │
                │ ④ Response (sync)                         │
                │    {JSON-RPC response}                    │
                ◀────────────────────────────────────────┤
                │                                           │
┌───────────────┴───────────────────────────────────────────┐
│              SERVIDOR WINDMILL                             │
│  https://statutes-britain-find-sister.trycloudflare.com   │
└────────────────────────────────────────────────────────────┘
```

## Passo 1️⃣: Estabelecer Conexão SSE

### Cliente Conecta ao SSE

```bash
GET /mcp/{mcp_id}/sse
Authorization: Bearer {api_key}
```

### Servidor Responde com Eventos

```
event: endpoint
data: /mcp/{mcp_id}/message

event: connected
data: {"mcp_id": "abc123", "protocol_version": "2024-11-05"}

event: ping
data: {"timestamp": 1234567890}
```

### ⚠️ Evento Crítico: `endpoint`

Este evento **DEVE** ser enviado no início da conexão para informar ao cliente onde enviar mensagens:

```
event: endpoint
data: /mcp/{mcp_id}/message
```

**Sem este evento, o cliente não saberá para onde enviar os POSTs!**

## Passo 2️⃣: Enviar Mensagens (JSON-RPC 2.0)

### Cliente Envia Requisição POST

```bash
POST /mcp/{mcp_id}/message
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

### Servidor Responde Sincronamente

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "Windmill MCP",
      "version": "1.0.0"
    }
  }
}
```

## Métodos MCP Disponíveis

### 1. `initialize` - Inicialização

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {"name": "Windmill MCP", "version": "1.0.0"}
  }
}
```

### 2. `tools/list` - Listar Ferramentas

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "nmap",
        "description": "Network scanning tool",
        "inputSchema": {
          "type": "object",
          "properties": {
            "target": {
              "type": "string",
              "description": "IP or hostname to scan"
            }
          },
          "required": ["target"]
        }
      }
    ]
  }
}
```

### 3. `tools/call` - Executar Ferramenta

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "nmap",
    "arguments": {
      "target": "192.168.1.1",
      "flags": "-sV"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "PORT     STATE SERVICE VERSION\n22/tcp   open  ssh     OpenSSH 8.2"
      }
    ],
    "isError": false
  }
}
```

## Autenticação

Todas as requisições precisam do header:

```
Authorization: Bearer {api_key}
```

O `api_key` é gerado ao criar um MCP Server no Windmill.

## Exemplo Completo em Python

```python
import requests
import json
import sseclient  # pip install sseclient-py

# Configuração
MCP_ID = "seu-mcp-id"
API_KEY = "sua-api-key"
BASE_URL = "https://statutes-britain-find-sister.trycloudflare.com"

# 1. Conectar ao SSE
sse_url = f"{BASE_URL}/mcp/{MCP_ID}/sse"
headers = {"Authorization": f"Bearer {API_KEY}"}

response = requests.get(sse_url, headers=headers, stream=True)
client = sseclient.SSEClient(response)

# 2. Ler eventos
endpoint_url = None
for event in client.events():
    if event.event == "endpoint":
        endpoint_url = BASE_URL + event.data
        print(f"Endpoint descoberto: {endpoint_url}")
        break

# 3. Enviar mensagens
def send_message(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    resp = requests.post(endpoint_url, json=payload, headers=headers)
    return resp.json()

# 4. Usar o MCP
init_result = send_message("initialize")
print("Inicializado:", init_result)

tools_result = send_message("tools/list")
print("Ferramentas:", tools_result)

call_result = send_message("tools/call", {
    "name": "nmap",
    "arguments": {"target": "scanme.nmap.org"}
})
print("Resultado:", call_result)
```

## Exemplo em Node.js

```javascript
const EventSource = require('eventsource');
const fetch = require('node-fetch');

const MCP_ID = 'seu-mcp-id';
const API_KEY = 'sua-api-key';
const BASE_URL = 'https://statutes-britain-find-sister.trycloudflare.com';

// 1. Conectar ao SSE
const sseUrl = `${BASE_URL}/mcp/${MCP_ID}/sse`;
const eventSource = new EventSource(sseUrl, {
  headers: { Authorization: `Bearer ${API_KEY}` }
});

let endpointUrl = null;

eventSource.addEventListener('endpoint', (event) => {
  endpointUrl = BASE_URL + event.data;
  console.log('Endpoint:', endpointUrl);
  
  // 2. Inicializar
  sendMessage('initialize').then(console.log);
});

async function sendMessage(method, params = {}) {
  const response = await fetch(endpointUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method,
      params
    })
  });
  return response.json();
}
```

## Fluxo de Erro

Se houver erro, a resposta JSON-RPC terá um campo `error`:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Additional error details"
  }
}
```

### Códigos de Erro JSON-RPC

| Código | Nome | Descrição |
|--------|------|-----------|
| -32700 | Parse error | JSON inválido |
| -32600 | Invalid Request | Requisição malformada |
| -32601 | Method not found | Método não existe |
| -32602 | Invalid params | Parâmetros inválidos |
| -32603 | Internal error | Erro interno do servidor |

## URLs de Produção

- **Base**: `https://statutes-britain-find-sister.trycloudflare.com`
- **SSE**: `https://statutes-britain-find-sister.trycloudflare.com/mcp/{mcp_id}/sse`
- **POST**: `https://statutes-britain-find-sister.trycloudflare.com/mcp/{mcp_id}/message`

## Checklist para Integração

- [ ] Obter API Key do MCP Server
- [ ] Conectar ao endpoint SSE
- [ ] Aguardar evento `endpoint`
- [ ] Enviar `initialize` para configurar
- [ ] Listar ferramentas com `tools/list`
- [ ] Executar ferramentas com `tools/call`
- [ ] Tratar erros JSON-RPC apropriadamente
