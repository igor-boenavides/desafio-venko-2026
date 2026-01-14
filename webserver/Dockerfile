# Função: Instruções para o Docker criar uma imagem customizada do webserver.

FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
RUN pip install --no-cache-dir flask psycopg2-binary gunicorn

# Copiar arquivos da aplicação
COPY app.py .
COPY templates templates/

# Expor porta 80
EXPOSE 80

# Executar aplicação com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "app:app"]