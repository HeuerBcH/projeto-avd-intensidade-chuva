Write-Host 'Atualizando Grafana com integracao ML...' -ForegroundColor Cyan
Write-Host ''

# 1. Cria tabela e views ML
Write-Host '[1/3] Criando tabela e views ML no PostgreSQL...' -ForegroundColor Yellow
$sqlML = 'sql_scripts\05_setup_ml_grafana.sql'
if (Test-Path $sqlML) {
    try {
        Get-Content $sqlML | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'OK: Tabela e views ML criadas!' -ForegroundColor Green
        } else {
            Write-Host 'AVISO: Pode ter havido erros na criacao' -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "ERRO: Arquivo nao encontrado: $sqlML" -ForegroundColor Red
}

Write-Host ''

# 2. Recarrega views do Grafana (incluindo as novas)
Write-Host '[2/3] Recriando todas as views do Grafana...' -ForegroundColor Yellow
$sqlViews = 'sql_scripts\04_views_grafana.sql'
if (Test-Path $sqlViews) {
    try {
        Get-Content $sqlViews | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'OK: Views do Grafana atualizadas!' -ForegroundColor Green
        } else {
            Write-Host 'AVISO: Pode ter havido erros na atualizacao' -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "ERRO: Arquivo nao encontrado: $sqlViews" -ForegroundColor Red
}

Write-Host ''

# 3. Reinicia Grafana para recarregar dashboard
Write-Host '[3/3] Reiniciando Grafana para recarregar dashboard...' -ForegroundColor Yellow
try {
    docker restart grafana
    Write-Host 'OK: Grafana reiniciado!' -ForegroundColor Green
    Write-Host '   Aguarde 10-15 segundos para o Grafana iniciar...' -ForegroundColor Gray
    Start-Sleep -Seconds 5
} catch {
    Write-Host "ERRO ao reiniciar Grafana: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'Atualizacao concluida!' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Proximos passos:' -ForegroundColor Yellow
Write-Host '  1. Execute: .\gerar_predicoes_ml.ps1' -ForegroundColor White
Write-Host '     (Isso vai gerar predicoes ML para popular os paineis)' -ForegroundColor Gray
Write-Host '  2. Acesse: http://localhost:3000' -ForegroundColor White
Write-Host '  3. Faca login: admin / admin' -ForegroundColor White
Write-Host '  4. Vá em Dashboards > Intensidade de Chuva - INMET' -ForegroundColor White
Write-Host '  5. Role para baixo para ver os novos paineis ML (🤖)' -ForegroundColor White
Write-Host ''
Write-Host 'Para gerar predicoes ML manualmente:' -ForegroundColor Yellow
Write-Host '  .\gerar_predicoes_ml.ps1' -ForegroundColor Gray
Write-Host '  Ou: POST http://localhost:8000/predict-from-db?limit=100' -ForegroundColor Gray
Write-Host ''

