# 🔐 Enterprise Security Architecture

A segurança não é uma "feature" no ContextWorks; é a base da arquitetura. Este documento detalha os controles implementados para garantir a integridade de ambientes corporativos.

## 1. Modelo de Ameaça Zero-Trust

Assumimos que nenhuma ferramenta é confiável e nenhum ambiente de execução deve persistir.

### Isolamento de Workload
Cada execução de ferramenta ocorre em um **Namespace Kubernetes** dedicado (configurável), dentro de um Pod com:
- **Resource Quotas**: Limites estritos de CPU e Memória para evitar "vizinhos barulhentos" ou DoS.
- **Network Policies**: Por padrão, o Pod de execução não tem acesso à internet (egress deny-all), a menos que explicitamente permitido na definição da ferramenta.

## 2. Autenticação e Autorização (RBAC)

### Identidade
- **Humanos**: Autenticação via JWT (JSON Web Tokens). Suporte planejado para OIDC/SAML (SSO).
- **Máquinas/Agentes**: API Keys rotacionáveis com escopos limitados.

### Role-Based Access Control
O ContextWorks define três papeis principais:
1.  **Admin**: Pode criar/deletar ferramentas e gerenciar usuários.
2.  **Operator**: Pode executar ferramentas e ver logs.
3.  **Auditor**: Apenas leitura de logs de execução (compliance).

## 3. Gestão de Segredos

O ContextWorks **nunca** armazena segredos de infraestrutura (senhas de banco, chaves AWS) em seu banco de dados de aplicação em texto plano.

### Integração com Kubernetes Secrets
As ferramentas recebem segredos via injeção de variáveis de ambiente no momento da criação do Pod. O Backend mapeia segredos do Vault ou K8s Secrets diretamente para o container da ferramenta, sem que o valor passe pelo frontend ou CLI.

## 4. Auditoria e Compliance

Todas as ações são registradas em trilhas de auditoria imutáveis.

### O que é registrado?
- **Quem**: ID do usuário ou Agente.
- **O Que**: ID da ferramenta e argumentos exatos fornecidos.
- **Quando**: Timestamp UTC de início e fim.
- **Resultado**: Código de saída (exit code) e logs completos (stdout/stderr).

### Retenção
Os logs são streamados para armazenamento persistente (S3/Blob Storage configurável) e podem ser retidos por N anos para fins legais.
