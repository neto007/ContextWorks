# 📘 Referência de Comandos

O **ContextWorks CLI** segue um padrão robusto de subcomandos. Esta página detalha cada comando, suas flags e exemplos de uso.

## Comandos Globais (Persistent Flags)

Estas flags podem ser usadas com qualquer subcomando:

- `--json`: Retorna a saída do comando em formato JSON. Ideal para automação.
- `--debug`: Habilita logs detalhados para depuração.
- `--help` / `-h`: Exibe a ajuda para o comando.

---

## 🔐 login

Autentica o usuário no servidor e salva as credenciais localmente.

### Uso
```bash
contextworks login [flags]
```

### Flags
- `--url` / `-u`: URL base do servidor (Padrão: `http://localhost:8001`)
- `--context` / `-c`: Nome do perfil para salvar as credenciais (ex: `prod`, `dev`)

### Exemplo
```bash
contextworks login --url https://api.contextworks.com --context prod
```
*O comando solicitará Email e Senha interativamente.*

---

## 🔄 sync

Sincroniza scripts Python locais com o servidor.

### Uso
```bash
contextworks sync [flags]
```

### Flags
- `--dir` / `-d`: Diretório contendo os scripts (Padrão: `.`)
- `--url` / `-u`: URL do servidor (Sobrescreve a URL do contexto)
- `--token` / `-t`: Token de autenticação manual
- `--prune` / `-p`: Deleta no servidor as ferramentas que não existem localmente
- `--build` / `-b`: Gatilha o build automático para ferramentas novas ou atualizadas

### Estrutura de Diretório Requerida
```text
pasta-scripts/
├── categoria-a/
│   ├── script1.py
│   └── script2.py
└── categoria-b/
    └── script3.py
```

---

## 📥 pull

Baixa todos os scripts e ferramentas do servidor para o sistema de arquivos local.

### Uso
```bash
contextworks pull [flags]
```

### Flags
- `--dir` / `-d`: Diretório de destino para os scripts
- `--url` / `-u`: URL do servidor
- `--token` / `-t`: Token de autenticação manual

---

## 👤 whoami

Exibe informações do usuário logado no contexto atual.

### Uso
```bash
contextworks whoami
```

---

## 🚪 logout

Remove as credenciais salvas localmente.

### Uso
```bash
contextworks logout
```

---

## 🆙 update

Verifica e instala a versão mais recente do CLI.

### Uso
```bash
contextworks update
```

---

## 📦 version

Exibe a versão instalada do CLI.

### Uso
```bash
contextworks version
```
