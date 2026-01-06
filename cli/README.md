# 🚀 ContextWorks CLI

[![Go Version](https://img.shields.io/github/go-mod/go-version/user/windmill-cli?color=00ADD8&logo=go)](https://go.dev/)
[![Enterprise Ready](https://img.shields.io/badge/Enterprise-Ready-blue.svg)](https://contextworks.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Interface de linha de comando robusta para sincronização e gerenciamento do ecossistema ContextWorks.

O **ContextWorks CLI** é o bridge oficial entre o seu ambiente de desenvolvimento local e o servidor ContextWorks. Ele permite que desenvolvedores gerenciem, sincronizem e versionem ferramentas e scripts Python com facilidade, integrando-se perfeitamente em pipelines de CI/CD.

## ✨ Principais Recursos

- 🔄 **Sincronização Bidirecional**: Sincronize scripts locais com o servidor (`sync`) ou baixe o estado atual (`pull`).
- 🛠️ **TUI Interativa**: Interface de terminal moderna usando BubbleTea para visualização em tempo real.
- 🔐 **Gestão de Contextos**: Alterne facilmente entre ambientes (dev, staging, prod).
- 📦 **Estrutura Baseada em Categorias**: Organização automática baseada na sua estrutura de diretórios.
- 🚀 **Performance**: Compilado em Go para execução instantânea e cross-platform.

---

## 🚀 Instalação Rápida

Para instalar o CLI em seu sistema Linux:

```bash
# Clone e entre no diretório do CLI
cd contextworks/cli

# Compile e instale globalmente
make install
```

---

## 📖 Como Usar

### Autenticação
Primeiro, realize o login para configurar seu contexto padrão:
```bash
contextworks login --url http://api.contextworks.local
```

### Sincronização de Scripts
Para enviar seus scripts locais para o servidor:
```bash
contextworks sync --dir ./meus-scripts
```

### Recuperação de Código
Para recriar sua estrutura local a partir do servidor:
```bash
contextworks pull --dir ./restore
```

---

## 📂 Documentação Detalhada

Para informações aprofundadas, consulte nossos guias:

| Guia | Descrição |
| :--- | :--- |
| [📘 Referência de Comandos](docs/commands.md) | Detalhes de todas as flags e subcomandos. |
| [💡 Conceitos Core](docs/concepts.md) | Entenda como funciona a sincronização e os contextos. |
| [🏗️ Arquitetura](docs/architecture.md) | Visão técnica sobre a implementação e estrutura. |

---

## 🛠️ Desenvolvimento

Consulte o [Makefile](Makefile) para ver os targets disponíveis para build, teste e instalação.

---

© 2026 ContextWorks Team. Enterprise Grade Script Management.
