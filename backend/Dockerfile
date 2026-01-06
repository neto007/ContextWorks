FROM python:3.9-slim

# Instalar uv (package manager moderno)
RUN pip install uv

WORKDIR /app

# Copiar arquivos de dependências
COPY pyproject.toml ./

# Instalar dependências com uv
RUN uv pip install --system -r pyproject.toml

# Copiar código da aplicação
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
