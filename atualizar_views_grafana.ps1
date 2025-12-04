Write-Host 'Atualizando views do Grafana para evitar "no data"...' -ForegroundColor Cyan
Write-Host ''

# Recria todas as views do Grafana
Write-Host '[1/2] Recriando views do Grafana...' -ForegroundColor Yellow
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

# Reinicia Grafana
Write-Host '[2/2] Reiniciando Grafana...' -ForegroundColor Yellow
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
Write-Host 'Agora os paineis devem mostrar valores (mesmo que zero)' -ForegroundColor Green
Write-Host '   ao inves de "no data"' -ForegroundColor Green
Write-Host ''
Write-Host 'Acesse: http://localhost:3000' -ForegroundColor White
Write-Host '   Dashboard: Intensidade de Chuva - INMET' -ForegroundColor White
Write-Host ''

