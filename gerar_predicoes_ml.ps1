Write-Host 'Gerando predicoes ML para popular o Grafana...' -ForegroundColor Cyan
Write-Host ''

# Verifica se FastAPI está disponível
Write-Host 'Verificando FastAPI...' -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/' -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host 'OK: FastAPI esta disponivel!' -ForegroundColor Green
    }
} catch {
    Write-Host 'ERRO: FastAPI nao esta disponivel em http://localhost:8000' -ForegroundColor Red
    Write-Host '   Execute: docker compose up -d' -ForegroundColor Yellow
    exit 1
}

Write-Host ''

# Verifica se há dados no banco
Write-Host 'Verificando dados no banco...' -ForegroundColor Yellow
try {
    $dadosCount = docker exec postgres-inmet psql -U inmet_user -d inmet_db -t -c "SELECT COUNT(*) FROM dados_meteorologicos WHERE intensidade_chuva IS NOT NULL;" 2>&1
    $dadosCount = ($dadosCount -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1).Trim()
    
    if ($dadosCount -and [int]$dadosCount -gt 0) {
        Write-Host "OK: Encontrados $dadosCount registros classificados no banco" -ForegroundColor Green
    } else {
        Write-Host 'AVISO: Nenhum dado classificado encontrado no banco' -ForegroundColor Yellow
        Write-Host '   Execute primeiro: POST http://localhost:8000/ingest-from-thingsboard' -ForegroundColor Gray
        Write-Host '   E depois: .\executar_sql.ps1 sql_scripts\03_update_intensidade_chuva.sql' -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host 'ERRO ao verificar banco de dados' -ForegroundColor Red
    exit 1
}

Write-Host ''

# Verifica se o modelo ML está carregado
Write-Host 'Verificando modelo ML...' -ForegroundColor Yellow
try {
    $modelResponse = Invoke-WebRequest -Uri 'http://localhost:8000/models/info' -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($modelResponse.StatusCode -eq 200) {
        $modelInfo = $modelResponse.Content | ConvertFrom-Json
        if ($modelInfo.model_info.loaded) {
            Write-Host "OK: Modelo ML carregado: $($modelInfo.model_info.model_name)" -ForegroundColor Green
        } else {
            Write-Host 'AVISO: Modelo ML nao esta carregado. Tentando carregar...' -ForegroundColor Yellow
            try {
                $loadResponse = Invoke-WebRequest -Uri 'http://localhost:8000/models/load' -Method POST -TimeoutSec 10 -UseBasicParsing
                if ($loadResponse.StatusCode -eq 200) {
                    Write-Host 'OK: Modelo ML carregado com sucesso!' -ForegroundColor Green
                }
            } catch {
                Write-Host 'ERRO: Nao foi possivel carregar o modelo ML' -ForegroundColor Red
                Write-Host '   Execute primeiro o notebook: notebooks/03_modelagem_mlflow.ipynb' -ForegroundColor Yellow
                exit 1
            }
        }
    }
} catch {
    Write-Host 'AVISO: Nao foi possivel verificar modelo. Continuando...' -ForegroundColor Yellow
}

Write-Host ''

# Gera predições
Write-Host 'Gerando predicoes ML...' -ForegroundColor Yellow
Write-Host '   (Isso pode levar alguns minutos dependendo da quantidade de dados)' -ForegroundColor Gray

$limit = 100  # Gera predições para os 100 registros mais recentes
try {
    Write-Host "   Gerando predicoes para $limit registros..." -ForegroundColor Gray
    $predictResponse = Invoke-WebRequest -Uri "http://localhost:8000/predict-from-db?limit=$limit" -Method POST -TimeoutSec 300 -UseBasicParsing
    
    if ($predictResponse.StatusCode -eq 200) {
        $result = $predictResponse.Content | ConvertFrom-Json
        $total = $result.total
        
        if ($total -gt 0) {
            Write-Host "OK: $total predicoes ML geradas com sucesso!" -ForegroundColor Green
        } else {
            Write-Host 'AVISO: Nenhuma predicao foi gerada' -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "ERRO ao gerar predicoes: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host '   Verifique se o modelo ML esta treinado e carregado' -ForegroundColor Yellow
    exit 1
}

Write-Host ''

# Verifica predições geradas
Write-Host 'Verificando predicoes no banco...' -ForegroundColor Yellow
try {
    $predCount = docker exec postgres-inmet psql -U inmet_user -d inmet_db -t -c "SELECT COUNT(*) FROM predicoes_intensidade;" 2>&1
    $predCount = ($predCount -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1).Trim()
    
    if ($predCount -and [int]$predCount -gt 0) {
        Write-Host "OK: $predCount predicoes ML encontradas no banco!" -ForegroundColor Green
    } else {
        Write-Host 'AVISO: Nenhuma predicao encontrada no banco' -ForegroundColor Yellow
    }
} catch {
    Write-Host 'AVISO: Nao foi possivel verificar predicoes' -ForegroundColor Yellow
}

Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'Processo concluido!' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Agora os paineis ML no Grafana devem mostrar dados!' -ForegroundColor Green
Write-Host '   Acesse: http://localhost:3000' -ForegroundColor White
Write-Host '   Dashboard: Intensidade de Chuva - INMET' -ForegroundColor White
Write-Host ''
Write-Host 'Para gerar mais predicoes:' -ForegroundColor Yellow
Write-Host '   .\gerar_predicoes_ml.ps1' -ForegroundColor Gray
Write-Host '   Ou: POST http://localhost:8000/predict-from-db?limit=200' -ForegroundColor Gray
Write-Host ''

