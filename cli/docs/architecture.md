# 🏗️ Arquitetura do Sistema

Esta página detalha a estrutura interna e as decisões tecnológicas do **ContextWorks CLI**.

## Pilha Tecnológica

- **Linguagem**: Go (Golang)
- **Framework de CLI**: [Cobra](https://github.com/spf13/cobra) - Padrão de mercado para CLI robustos.
- **TUI Framework**: [BubbleTea](https://github.com/charmbracelet/bubbletea) - Motor para interfaces de terminal baseadas em ELM architecture.
- **HTTP Client**: Implementação customizada em Go para lidar com autenticação e streams.

## Estrutura de Pastas

O código está organizado para separação de preocupações:

```text
cli/
├── main.go           # Ponto de entrada e definição do RootCmd
├── cmd_*.go          # Definições de subcomandos (sync, pull, login...)
├── sync_logic.go     # Core engine de sincronização
└── pkg/
    ├── config/       # Gestão de arquivos de configuração e contextos
    ├── httpclient/   # Wrapper para requisições com autenticação
    ├── logger/       # Utilitários de log (suporte a cores e JSON)
    ├── tui/          # Componentes BubbleTea para interface visual
    └── validator/    # Lógica de validação de diretórios e arquivos
```

## Fluxo de Sincronização (`sync`)

O processo de sincronização segue este pipeline:

1. **Load Config**: Carrega o contexto atual e o token de acesso.
2. **Scan Directory**: Varre o diretório `--dir` recursivamente.
3. **Filter**: Identifica arquivos `.py` válidos e mapeia suas categorias.
4. **Interactive Init**: Inicia o programa BubbleTea (caso não esteja em modo JSON).
5. **Diffing**: Faz requisições HEAD/GET ao servidor para verificar quais arquivos precisam ser alterados.
6. **Parallel Uploads**: Realiza o upload dos scripts em concorrência controlada.
7. **Pruning (opcional)**: Se `--prune` estiver ativo, solicita ao servidor a exclusão de IDs órfãos.
8. **Summary**: Exibe o relatório final de operações realizadas.

## Extensibilidade

O CLI foi desenhado para ser facilmente estensível. Novos comandos podem ser adicionados criando um novo arquivo `cmd_nome.go` e registrando o comando no `init()` do `main.go`.

Para contribuir, certifique-se de manter a compatibilidade com o formato de saída JSON para garantir que integrações existentes não sejam quebradas.
