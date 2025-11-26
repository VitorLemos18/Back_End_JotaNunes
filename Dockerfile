FROM python:3.11-slim

# Instalar dependências e mssql-tools + drivers ODBC
# Instalar dependências e mssql-tools + drivers ODBC
RUN apt-get update && \
    apt-get install -y curl gnupg unixodbc unixodbc-dev && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg && \
    chmod 644 /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/config/debian/12/prod.list /" \
        > /etc/apt/sources.list.d/mssql-release.list && \
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
