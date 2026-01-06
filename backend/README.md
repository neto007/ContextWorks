# 🛡️ ContextWorks Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Native-326CE5?logo=kubernetes)](https://kubernetes.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org)

> O núcleo de segurança e orquestração da plataforma ContextWorks.

O Backend do ContextWorks é um serviço de alta performance construído com **FastAPI**, projetado para orquestrar a execução segura de ferramentas de segurança em clusters Kubernetes. Ele serve como a fonte da verdade para ferramentas, gerencia autenticação e coordena jobs assíncronos.

## ✨ Principais Recursos

- 🚀 **Performance Assíncrona**: Construído sobre ASGI para lidar com milhares de conexões simultâneas.
- 🐳 **Execução Isolada**: Cada ferramenta roda em seu próprio Pod/Job Kubernetes efêmero via `execution_service`.
- 🔐 **Segurança Enterprise**: Autenticação JWT robusta e RBAC (Role-Based Access Control).
- 📡 **Protocolo MCP**: Implementação nativa do *Model Context Protocol* para integração com LLMs.
- 📦 **Gestão de Ferramentas**: Scanner automático de scripts Python e metadados YAML.

---

## 🚀 Como Iniciar

### Pré-requisitos
- Python 3.12+
- Docker & Kubernetes (Minikube ou Kind para local)
- PostgreSQL
- Gerenciador de pacotes `uv` (recomendado)

### Setup Local

```bash
# Entre na pasta do backend
cd contextworks/backend

# Instale as dependências e crie o venv
uv sync

# Ative o ambiente virtual
source .venv/bin/activate
```

### Configuração
Crie um arquivo `.env` ou exporte as variáveis:

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/contextworks"
export K8S_NAMESPACE="contextworks-platform"
export SECRET_KEY="sua_chave_secreta_aqui"
```

### Executando o Servidor

```bash
# Modo de desenvolvimento com reload
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse a documentação interativa em: `http://localhost:8000/docs`

---

## 📂 Documentação Detalhada

Para aprofundar seu conhecimento na arquitetura e operações:

| Guia | Descrição |
| :--- | :--- |
| [🏗️ Arquitetura](docs/architecture.md) | Camadas Core vs Services, Injeção de Dependências e DB. |
| [🚀 Deployment & K8s](docs/deployment.md) | Guia de operações, configuração de Pods e Variáveis de Ambiente. |
| [🛠️ Sistema de Ferramentas](docs/tools_system.md) | Como criar, registrar e executar ferramentas Python. |
| [🔌 Referência de API](docs/api_reference.md) | Detalhamento dos endpoints e protocolo MCP. |

---

## 🧪 Testes

Execute a suíte de testes unitários e de integração:

```bash
uv run pytest
```

---

© 2026 ContextWorks Team. Secure Orchestration Platform.
