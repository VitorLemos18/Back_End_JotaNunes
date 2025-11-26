FROM python:3.11-slim

# Instalar dependências e mssql-tools + drivers ODBC
RUN apt-get update && \
    apt-get install -y curl gnupg unixodbc unixodbc-dev && \
    curl -fsSL https://packages.microsoft.com/config/packages-microsoft-prod.deb -o packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 && \
    echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD gunicorn jn_custom.wsgi:application --bind 0.0.0.0:${PORT:-8000}
