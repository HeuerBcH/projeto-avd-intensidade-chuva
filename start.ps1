Write-Host "  Pipeline INMET - Iniciando Servicos" -ForegroundColor Cyan
Write-Host ""

# Verifica se o Docker está rodando
Write-Host "Verificando Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "Docker está rodando!" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Docker não está rodando. Por favor, inicie o Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verifica se o arquivo .env existe
$envFile = "fastapi/app/.env"
if (-not (Test-Path $envFile)) {
    Write-Host "Criando arquivo .env..." -ForegroundColor Yellow
    @"
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

# Configurações do ThingsBoard
THINGSBOARD_HOST=http://thingsboard:9090
THINGSBOARD_USER=tenant@thingsboard.org
THINGSBOARD_PASSWORD=tenant
"@ | Out-File -FilePath $envFile -Encoding utf8
    Write-Host "Arquivo .env criado!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Iniciando containers Docker..." -ForegroundColor Yellow
docker compose up -d

Write-Host ""
Write-Host "Aguardando serviços iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "  Servicos Iniciados!" -ForegroundColor Green
Write-Host ""
Write-Host "Acesse os seguintes serviços:" -ForegroundColor Cyan
Write-Host "  - FastAPI:        http://localhost:8000" -ForegroundColor White
Write-Host "  - ThingsBoard:    http://localhost:9090 (tenant@thingsboard.org/tenant)" -ForegroundColor White
Write-Host "  - JupyterLab:     http://localhost:1010 (token: avd2025)" -ForegroundColor White
Write-Host "  - MLFlow:         http://localhost:5000" -ForegroundColor White
Write-Host "  - Trendz:         http://localhost:8888" -ForegroundColor White
Write-Host "  - MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor White
Write-Host "  - PostgreSQL:     localhost:5432" -ForegroundColor White
Write-Host ""
Write-Host "Para ver os logs: docker compose logs -f" -ForegroundColor Yellow
Write-Host "Para parar: docker compose down" -ForegroundColor Yellow

