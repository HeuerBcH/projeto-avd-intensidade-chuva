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
            Write-Host 'OK: FastAPI esta pronto!' -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "   Aguardando FastAPI... ($i/30)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

# Aguarda PostgreSQL estar pronto
Write-Host 'Verificando PostgreSQL...' -ForegroundColor Yellow
$postgresReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $result = docker exec postgres-inmet pg_isready -U inmet_user -d inmet_db 2>&1
        if ($LASTEXITCODE -eq 0) {
            $postgresReady = $true
            Write-Host 'OK: PostgreSQL esta pronto!' -ForegroundColor Green
            break
        }
    } catch {
        # Continua tentando
    }
    Write-Host "   Aguardando PostgreSQL... ($i/30)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($fastapiReady -and $postgresReady) {
    Write-Host ''
    Write-Host 'Inicializando pipeline automatico completo...' -ForegroundColor Cyan
    Write-Host '   (Isso pode levar alguns minutos na primeira execução)' -ForegroundColor Gray
    Write-Host ''
    
    # 1. Executa script de inicialização (ThingsBoard → S3 → PostgreSQL)
    $initScript = 'fastapi\app\scripts\init_pipeline.py'
    if (Test-Path $initScript) {
        Write-Host '   [1/4] Executando script de inicialização do pipeline...' -ForegroundColor Gray
        try {
            # Aguarda um pouco mais para garantir que o FastAPI está totalmente pronto
            Start-Sleep -Seconds 5
            
            # Executa o script dentro do container
            docker exec fastapi-ingestao python /app/scripts/init_pipeline.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host 'OK: Pipeline inicializado com sucesso!' -ForegroundColor Green
            } else {
                Write-Host 'AVISO: Pipeline pode nao ter sido inicializado completamente' -ForegroundColor Yellow
            }
        } catch {
            Write-Host 'AVISO: Nao foi possivel executar inicializacao automatica' -ForegroundColor Yellow
        }
    } else {
        Write-Host "AVISO: Script de inicializacao nao encontrado em: $initScript" -ForegroundColor Yellow
    }
    
    # Aguarda um pouco para garantir que os dados foram inseridos
    Write-Host ''
    Write-Host '   Aguardando dados serem processados...' -ForegroundColor Gray
    Start-Sleep -Seconds 10
    
    # Verifica se há dados no banco antes de executar scripts SQL
    Write-Host '   Verificando se há dados no banco...' -ForegroundColor Gray
    $dadosCount = docker exec postgres-inmet psql -U inmet_user -d inmet_db -t -c "SELECT COUNT(*) FROM dados_meteorologicos;" 2>&1
    $dadosCount = ($dadosCount -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1).Trim()
    
    if ($dadosCount -and [int]$dadosCount -gt 0) {
        Write-Host "   OK: Encontrados $dadosCount registros no banco" -ForegroundColor Green
        
        # 2. Classifica intensidade de chuva
        $sqlClassificacao = 'sql_scripts\03_update_intensidade_chuva.sql'
        if (Test-Path $sqlClassificacao) {
            Write-Host '   [2/4] Classificando intensidade de chuva...' -ForegroundColor Gray
            try {
                Get-Content $sqlClassificacao | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host 'OK: Classificacao de intensidade concluida!' -ForegroundColor Green
                } else {
                    Write-Host 'AVISO: Classificacao pode nao ter sido aplicada completamente' -ForegroundColor Yellow
                }
            } catch {
                Write-Host 'AVISO: Erro ao executar classificacao de intensidade' -ForegroundColor Yellow
            }
        } else {
            Write-Host "AVISO: Script SQL nao encontrado: $sqlClassificacao" -ForegroundColor Yellow
        }
    } else {
        Write-Host '   AVISO: Nenhum dado encontrado no banco. Scripts SQL serao pulados.' -ForegroundColor Yellow
        Write-Host '   Dica: Coloque arquivos CSV em fastapi/app/data/raw/ e execute:' -ForegroundColor Gray
        Write-Host '      POST http://localhost:8000/populate-thingsboard' -ForegroundColor Gray
        Write-Host '      POST http://localhost:8000/ingest-from-thingsboard' -ForegroundColor Gray
    }
    
    # 3. Cria views para Grafana (sempre executa, mesmo sem dados)
    $sqlViews = 'sql_scripts\04_views_grafana.sql'
    if (Test-Path $sqlViews) {
        Write-Host '   [3/4] Criando views para Grafana...' -ForegroundColor Gray
        try {
            Get-Content $sqlViews | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host 'OK: Views do Grafana criadas com sucesso!' -ForegroundColor Green
            } else {
                Write-Host 'AVISO: Views podem nao ter sido criadas completamente' -ForegroundColor Yellow
            }
        } catch {
            Write-Host 'AVISO: Erro ao criar views do Grafana' -ForegroundColor Yellow
        }
    } else {
        Write-Host "AVISO: Script SQL nao encontrado: $sqlViews" -ForegroundColor Yellow
    }
    
    # 4. Verifica estatísticas finais
    Write-Host '   [4/4] Verificando estatísticas do banco...' -ForegroundColor Gray
    try {
        $stats = docker exec postgres-inmet psql -U inmet_user -d inmet_db -t -c "SELECT COUNT(*) FROM estacoes; SELECT COUNT(*) FROM dados_meteorologicos; SELECT COUNT(*) FROM dados_meteorologicos WHERE intensidade_chuva IS NOT NULL;"
        if ($LASTEXITCODE -eq 0) {
            $statsLines = $stats -split "`n" | Where-Object { $_.Trim() -ne '' }
            if ($statsLines.Count -ge 3) {
                $estacoes = $statsLines[0].Trim()
                $dados = $statsLines[1].Trim()
                $classificados = $statsLines[2].Trim()
                Write-Host "OK: Estatisticas: $estacoes estacoes, $dados registros, $classificados classificados" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host 'AVISO: Nao foi possivel obter estatisticas' -ForegroundColor Yellow
    }
    
    Write-Host ''
    Write-Host 'OK: Pipeline completo executado com sucesso!' -ForegroundColor Green
} else {
    if (-not $fastapiReady) {
        Write-Host 'AVISO: FastAPI nao esta disponivel. Pipeline nao sera inicializado automaticamente.' -ForegroundColor Yellow
    }
    if (-not $postgresReady) {
        Write-Host 'AVISO: PostgreSQL nao esta disponivel. Scripts SQL nao serao executados.' -ForegroundColor Yellow
    }
}

# Verifica se Grafana está disponível
Write-Host ''
Write-Host 'Verificando Grafana...' -ForegroundColor Yellow
$grafanaReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://localhost:3000/api/health' -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $grafanaReady = $true
            Write-Host 'OK: Grafana esta pronto!' -ForegroundColor Green
            break
        }
    } catch {
        # Continua tentando
    }
    Write-Host "   Aguardando Grafana... ($i/30)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $grafanaReady) {
    Write-Host 'AVISO: Grafana pode nao estar totalmente pronto ainda.' -ForegroundColor Yellow
    Write-Host '   Aguarde alguns segundos e acesse: http://localhost:3000' -ForegroundColor Gray
    Write-Host '   Login: admin / admin' -ForegroundColor Gray
} else {
    Write-Host '   Dashboard "Intensidade de Chuva - INMET" disponivel automaticamente!' -ForegroundColor Green
    Write-Host '   Acesse: Dashboards > Intensidade de Chuva - INMET' -ForegroundColor Gray
}

Write-Host ''
Write-Host 'Acesse os seguintes serviços:' -ForegroundColor Cyan
Write-Host '  - FastAPI:        http://localhost:8000' -ForegroundColor White
Write-Host '  - ThingsBoard:    http://localhost:9090 (tenant@thingsboard.org/tenant)' -ForegroundColor White
Write-Host '  - JupyterLab:     http://localhost:1010 (token: avd2025)' -ForegroundColor White
Write-Host '  - MLFlow:         http://localhost:5000' -ForegroundColor White
Write-Host '  - Grafana:        http://localhost:3000 (admin/admin) - Dashboard pronto!' -ForegroundColor White
Write-Host '  - MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)' -ForegroundColor White
Write-Host '  - PostgreSQL:     localhost:5432' -ForegroundColor White
Write-Host ''
Write-Host 'Endpoints uteis do FastAPI:' -ForegroundColor Cyan
Write-Host '  - Popular ThingsBoard: POST http://localhost:8000/populate-thingsboard' -ForegroundColor Gray
Write-Host '  - Ingerir dados:       POST http://localhost:8000/ingest-from-thingsboard' -ForegroundColor Gray
Write-Host '  - Estatísticas:        GET  http://localhost:8000/stats' -ForegroundColor Gray
Write-Host ''
Write-Host 'Para ver os logs: docker compose logs -f' -ForegroundColor Yellow
Write-Host 'Para parar: docker compose down' -ForegroundColor Yellow

