FROM mcr.microsoft.com/mssql-tools/python:3.11

# Instalar dependências essenciais
RUN apt-get update && \
    apt-get install -y unixodbc unixodbc-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD gunicorn jn_custom.wsgi:application --bind 0.0.0.0:${PORT:-8000}
