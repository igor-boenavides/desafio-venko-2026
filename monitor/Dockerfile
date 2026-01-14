# Função: Instruções para o Docker criar uma imagem customizada do monitor.

FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    iputils-ping \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
RUN pip install --no-cache-dir psycopg2-binary

# Copiar script de monitoramento
COPY monitor.py .

# Tornar o script executável
RUN chmod +x monitor.py

CMD ["python", "-u", "monitor.py"]