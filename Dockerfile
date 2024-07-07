# Use a imagem oficial do Python para o Flask
FROM python:3.9-slim

# Configuração inicial do ambiente
WORKDIR /app
COPY . /app

# Instalação das dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Porta em que o Flask vai rodar
EXPOSE 9090

# Comando para executar o Flask
CMD ["python", "app.py"]

# docker run -d -p 9090:9090 --env-file .env app-api
