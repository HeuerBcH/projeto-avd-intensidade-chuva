#!/bin/bash

# Script Bash para iniciar o pipeline completo
# Autor: Projeto AVD - Intensidade de Chuva

echo "========================================"
echo "  Pipeline INMET - Iniciando Servicos"
echo "========================================"
echo ""

# Verifica se o Docker está rodando
echo "Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "ERRO: Docker não está rodando. Por favor, inicie o Docker."
    exit 1
fi
echo "Docker está rodando!"
echo ""

# Verifica se o arquivo .env existe
ENV_FILE="fastapi/app/services/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Criando arquivo .env..."
    cat > "$ENV_FILE" << EOF
# Configurações do MinIO/S3
S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=inmet-data

# Configurações do PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=inmet_db
POSTGRES_USER=inmet_user
POSTGRES_PASSWORD=inmet_password
EOF
    echo "Arquivo .env criado!"
fi

echo ""
echo "Iniciando containers Docker..."
docker compose up -d

echo ""
echo "Aguardando serviços iniciarem..."
sleep 10

echo ""
echo "========================================"
echo "  Servicos Iniciados!"
echo "========================================"
echo ""
echo "Acesse os seguintes serviços:"
echo "  - FastAPI:        http://localhost:8000"
echo "  - JupyterLab:    http://localhost:1010 (token: avd2025)"
echo "  - MLFlow:         http://localhost:5000"
echo "  - Trendz:         http://localhost:8888"
echo "  - MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)"
echo "  - PostgreSQL:     localhost:5432"
echo ""
echo "Para ver os logs: docker compose logs -f"
echo "Para parar: docker compose down"






