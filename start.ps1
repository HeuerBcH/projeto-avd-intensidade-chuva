Write-Host '  Pipeline INMET - Iniciando Servicos' -ForegroundColor Cyan
Write-Host ''

# Verifica se o Docker está rodando
Write-Host 'Verificando Docker...' -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host 'Docker está rodando!' -ForegroundColor Green
} catch {
    Write-Host 'ERRO: Docker não está rodando. Por favor, inicie o Docker Desktop.' -ForegroundColor Red
    exit 1
}

Write-Host ''

# Verifica se o arquivo .env existe
$envFile = 'fastapi/app/.env'
if (-not (Test-Path $envFile)) {
    Write-Host 'Criando arquivo .env...' -ForegroundColor Yellow
    @'
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
'@ | Out-File -FilePath $envFile -Encoding utf8
    Write-Host 'Arquivo .env criado!' -ForegroundColor Green
}

Write-Host ''
Write-Host 'Iniciando containers Docker...' -ForegroundColor Yellow
docker compose up -d

Write-Host ''
Write-Host 'Aguardando serviços iniciarem...' -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ''
Write-Host '  Servicos Iniciados!' -ForegroundColor Green
Write-Host ''

# Verifica se FastAPI está disponível antes de executar o pipeline
Write-Host 'Verificando se FastAPI está pronto...' -ForegroundColor Yellow
$fastapiReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://localhost:8000/' -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $fastapiReady = $true
            Write-Host '✅ FastAPI está pronto!' -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "   Aguardando FastAPI... ($i/30)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if ($fastapiReady) {
    Write-Host ''
    Write-Host '🚀 Inicializando pipeline automático...' -ForegroundColor Cyan
    Write-Host '   (Isso pode levar alguns minutos na primeira execução)' -ForegroundColor Gray
    Write-Host ''
    
    # Executa script de inicialização
    $initScript = 'fastapi\app\scripts\init_pipeline.py'
    if (Test-Path $initScript) {
        Write-Host '   Executando script de inicialização...' -ForegroundColor Gray
        try {
            # Aguarda um pouco mais para garantir que o FastAPI está totalmente pronto
            Start-Sleep -Seconds 5
            
            # Executa o script dentro do container
            docker exec fastapi-ingestao python /app/scripts/init_pipeline.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host '✅ Pipeline inicializado com sucesso!' -ForegroundColor Green
            } else {
                Write-Host '⚠️  Pipeline pode não ter sido inicializado completamente' -ForegroundColor Yellow
                Write-Host '   Execute manualmente os endpoints:' -ForegroundColor Gray
                Write-Host '   1. POST http://localhost:8000/populate-thingsboard' -ForegroundColor Gray
                Write-Host '   2. POST http://localhost:8000/ingest-from-thingsboard' -ForegroundColor Gray
            }
        } catch {
            Write-Host '⚠️  Não foi possível executar inicialização automática' -ForegroundColor Yellow
            Write-Host '   Execute manualmente: docker exec fastapi-ingestao python /app/scripts/init_pipeline.py' -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️  Script de inicialização não encontrado em: $initScript" -ForegroundColor Yellow
        Write-Host '   Execute manualmente os endpoints:' -ForegroundColor Gray
        Write-Host '   1. POST http://localhost:8000/populate-thingsboard' -ForegroundColor Gray
        Write-Host '   2. POST http://localhost:8000/ingest-from-thingsboard' -ForegroundColor Gray
    }
} else {
    Write-Host '⚠️  FastAPI não está disponível. Pipeline não será inicializado automaticamente.' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Acesse os seguintes serviços:' -ForegroundColor Cyan
Write-Host '  - FastAPI:        http://localhost:8000' -ForegroundColor White
Write-Host '  - ThingsBoard:    http://localhost:9090 (tenant@thingsboard.org/tenant)' -ForegroundColor White
Write-Host '  - JupyterLab:     http://localhost:1010 (token: avd2025)' -ForegroundColor White
Write-Host '  - MLFlow:         http://localhost:5000' -ForegroundColor White
Write-Host '  - Grafana:        http://localhost:3000' -ForegroundColor White
Write-Host '  - MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)' -ForegroundColor White
Write-Host '  - PostgreSQL:     localhost:5432' -ForegroundColor White
Write-Host ''
Write-Host '📋 Endpoints úteis do FastAPI:' -ForegroundColor Cyan
Write-Host '  - Popular ThingsBoard: POST http://localhost:8000/populate-thingsboard' -ForegroundColor Gray
Write-Host '  - Ingerir dados:       POST http://localhost:8000/ingest-from-thingsboard' -ForegroundColor Gray
Write-Host '  - Estatísticas:        GET  http://localhost:8000/stats' -ForegroundColor Gray
Write-Host ''
Write-Host 'Para ver os logs: docker compose logs -f' -ForegroundColor Yellow
Write-Host 'Para parar: docker compose down' -ForegroundColor Yellow

