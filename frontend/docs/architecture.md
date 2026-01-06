# 🏗️ Arquitetura do Frontend

O design da aplicação segue o princípio de **Feature-First** combinado com uma camada de **Core/Shared** robusta.

## Estrutura de Diretórios

```text
src/
├── components/       # Componentes visuais
│   ├── layout/       # Componentes estruturais (Sidebar, Header)
│   ├── shared/       # Componentes reutilizáveis (Input, Button) - a maioria do Shadcn/UI
│   └── ui/           # Primitivos de UI
├── context/          # Context Providers (Auth, Theme)
├── hooks/            # Custom Hooks (useLogStream, useTools)
├── lib/              # Utilitários de terceiros configurados (utils.ts)
├── services/         # Camada de comunicação com API (Axios)
├── types/            # Definições de tipos TypeScript (Zod schemas e Interfaces)
├── styles/           # Configurações globais de CSS
└── App.tsx           # Entry point e roteamento principal
```

## Decisões Arquiteturais

### 1. Atomic Design Adaptado
Não seguimos o Atomic Design purista. Em vez disso, focamos em:
- **UI Components**: Componentes "burros" (presentational) que apenas recebem props. Ex: `Button`, `Card`.
- **Feature Components**: Componentes "inteligentes" que possuem lógica de negócio e conexão com dados. Ex: `ToolList`, `LogViewer`.

### 2. Gerenciamento de Estado
- **Server State**: Gerenciado via `React Query` (ou useEffect com hooks customizados em versões iniciais) para dados que vêm do backend.
- **Client State**: `React Context` para estados globais leves (Tema, Autenticação) e `useState`/`useReducer` para estados locais.

### 3. Roteamento
Utilizamos `React Router DOM v7`. As rotas são definidas centralizadamente no `App.tsx` (ou `routes.tsx`), protegidas por componentes de `AuthGuard` quando necessário.

## Padrões de Código

- **Componentes**: Function Components com Hooks.
- **Nomes de Arquivos**: PascalCase para componentes (`ToolCard.tsx`), camelCase para hooks e utils (`useAuth.ts`).
- **Exportações**: Preferimos `export function ComponentName` nomeados em vez de `export default` para facilitar refactoring.
