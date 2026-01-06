# 🛠️ Workflow de Desenvolvimento

Este guia descreve o processo passo-a-passo para adicionar novas funcionalidades ao frontend do ContextWorks.

## 1. Criando uma Nova Rota

Se a feature requer uma página dedicada:

1. Crie o componente da página em `src/pages/NomeDaPagina.tsx` (ou dentro de `src/components` se for pequeno).
2. Registre a rota no `App.tsx` (ou arquivo de rotas central):

```tsx
<Route path="/nova-rota" element={<NomeDaPagina />} />
```

## 2. Implementando a Lógica (Hooks/Services)

Antes de criar a UI, defina como os dados serão buscados.

1. Se for uma nova entidade API, crie `src/services/novaEntidadeService.ts`.
2. Crie um hook customizado se houver lógica de estado complexa: `src/hooks/useNovaEntidade.ts`.

## 3. Construindo a UI

1. Quebre a interface em componentes menores.
2. Identifique quais componentes base (`src/components/ui`) podem ser reutilizados (Cards, Buttons, Inputs).
3. Implemente o componente usando Tailwind para estilização.

## 4. Testando Localmente

Use o servidor de desenvolvimento para testar em tempo real:

```bash
npm run dev
```

Verifique:
- **Responsividade**: A interface quebra em telas menores?
- **Estados de Loading**: O usuário vê feedback enquanto os dados carregam?
- **Estados de Erro**: O que acontece se a API falhar?

## 5. Lint e Build

Antes de abrir o Pull Request, garanta que não há erros de lint ou build:

```bash
npm run lint
npm run build
```

Isso previne que erros de TypeScript bloqueiem o CI/CD.
