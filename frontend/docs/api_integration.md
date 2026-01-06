# 🔌 Integração com API

A comunicação com o Backend (FastAPI) é centralizada na pasta `src/services`, garantindo consistência no tratamento de erros e autenticação.

## Cliente HTTP (Axios)

Utilizamos uma instância configurada do Axios exportada de `src/lib/api.ts` (ou equivalent). Esta instância já possui:

- **Base URL**: Configurável via variável de ambiente `VITE_API_URL`.
- **Headers**: `Content-Type: application/json` padrão.
- **Interceptors**: Injeção automática do Bearer Token se disponível.

## Padrão de Serviço

Para cada entidade do domínio, existe um arquivo de serviço correspondente:

```typescript
// src/services/toolService.ts
import api from '@/lib/api';
import { Tool } from '@/types';

export const toolService = {
  getAll: async (): Promise<Tool[]> => {
    const { data } = await api.get('/tools');
    return data;
  },

  execute: async (toolId: string, params: Record<string, any>) => {
    return api.post(`/tools/${toolId}/execute`, params);
  }
};
```

## Tratamento de Erros

Erros da API devem ser tratados preferencialmente na camada de UI (componentes) ou através de um Error Boundary global, mas o serviço deve garantir que a exceção lançada seja tipada e contenha a mensagem amigável vinda do backend.

## Streaming de Logs

Para logs em tempo real (ex: execução de ferramentas), não usamos Axios. Utilizamos a API nativa `EventSource` (SSE - Server Sent Events) ou `WebSocket`, dependendo do endpoint.

**Exemplo de hook para SSE:**
```typescript
const useLogStream = (jobId: string) => {
  useEffect(() => {
    const eventSource = new EventSource(`${API_URL}/jobs/${jobId}/stream`);
    eventSource.onmessage = (event) => {
      // update logs state
    };
    return () => eventSource.close();
  }, [jobId]);
}
```
