# 🎨 ContextWorks Frontend

[![React](https://img.shields.io/badge/React-19.0-blue?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0-purple?logo=vite)](https://vitejs.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-4.0-cyan?logo=tailwindcss)](https://tailwindcss.com)

> O dashboard interativo moderno para gestão do ecossistema ContextWorks.

Esta aplicação é a interface visual para o gerenciamento de ferramentas, execução de scripts e monitoramento de logs do ContextWorks. Construída com as tecnologias mais recentes do ecossistema React para garantir performance, tipagem estática e uma experiência de desenvolvimento superior.

## ✨ Principais Recursos

- 🖥️ **Editor de Código Integrado**: Monaco Editor para visualização e edição rápida de scripts.
- ⚡ **Build Ultra Rápido**: Utiliza Vite para HMR (Hot Module Replacement) instantâneo.
- 💅 **Design System Moderno**: Tailwind CSS v4 com componentes Radix UI e ícones Lucide.
- 📡 **Comunicação Eficiente**: Integração com API RESTful via Axios com interceptors tipados.
- 🧩 **Arquitetura Modular**: Componentes isolados e reutilizáveis.

---

## 🚀 Como Iniciar

### Pré-requisitos
- Node.js (v20+)
- npm ou bun

### Instalação

```bash
# Entre na pasta do frontend
cd contextworks/frontend

# Instale as dependências
npm install
```

### Desenvolvimento Local

Para iniciar servidor de desenvolvimento em `http://localhost:5173`:

```bash
npm run dev
```

### Build de Produção

```bash
npm run build
# Para visualizar o build localmente:
npm run preview
```

---

## 📂 Documentação Detalhada

Para garantir a qualidade e padrão do código, consulte nossos guias técnicos:

| Guia | Descrição |
| :--- | :--- |
| [🏗️ Arquitetura](docs/architecture.md) | Estrutura de pastas, padrões de projeto e organização do código. |
| [🔌 Integração com API](docs/api_integration.md) | Como consumir o backend, tratar erros e tipar respostas. |
| [🎨 Guia de Estilos](docs/styling_guide.md) | Padrões de CSS/Tailwind, animações e componentes UI. |
| [flow Workflow de Dev](docs/development_workflow.md) | Passo-a-passo para criar novas features e componentes. |

---

## 🛠️ Stack Tecnológica

- **Core**: React 19, TypeScript
- **Build Tool**: Vite
- **Estilização**: Tailwind CSS v4, Tailwind Animate
- **Componentes**: Radix UI Primitives, Lucide React (Ícones)
- **Editor**: Monaco Editor React
- **HTTP Client**: Axios
- **Routing**: React Router DOM v7

---

© 2026 ContextWorks Team. Enterprise Grade Frontend Architecture.
