# Script PowerShell para configurar Trendz Analytics
# Configura datasource PostgreSQL automaticamente

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACAO DO TRENDZ ANALYTICS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se os containers estao rodando
Write-Host "Verificando containers..." -ForegroundColor Yellow
$containers = @("trendz", "thingsboard", "postgres-inmet", "fastapi")

foreach ($container in $containers) {
    $status = docker ps --filter "name=$container" --format "{{.Status}}"
    if ($status) {
        Write-Host "  OK: $container esta rodando" -ForegroundColor Green
    } else {
        Write-Host "  ERRO: $container nao esta rodando" -ForegroundColor Red
        Write-Host "     Execute: docker-compose up -d" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Aguardando servicos estarem prontos (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "Executando configuracao via FastAPI..." -ForegroundColor Cyan

# Executa configuração via endpoint FastAPI
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/configure-trendz" -Method POST -TimeoutSec 300
    
    if ($response.status -eq "success") {
        Write-Host ""
        Write-Host "OK: Configuracao concluida com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Proximos passos:" -ForegroundColor Cyan
        Write-Host "   1. Acesse Trendz: http://localhost:8888" -ForegroundColor White
        Write-Host "   2. Login: tenant@thingsboard.org / tenant" -ForegroundColor White
        Write-Host "   3. O datasource PostgreSQL ja deve estar configurado" -ForegroundColor White
        Write-Host "   4. Crie dashboards usando as views SQL:" -ForegroundColor White
        Write-Host "      - vw_dados_recentes" -ForegroundColor Gray
        Write-Host "      - vw_dados_7_dias" -ForegroundColor Gray
        Write-Host "      - vw_distribuicao_intensidade" -ForegroundColor Gray
        Write-Host "      - vw_ultimas_predicoes" -ForegroundColor Gray
        Write-Host "      - vw_comparacao_predicoes" -ForegroundColor Gray
        Write-Host ""
        
        if ($response.output) {
            Write-Host "Saida do script:" -ForegroundColor Cyan
            Write-Host $response.output -ForegroundColor Gray
        }
    } else {
        Write-Host ""
        Write-Host "AVISO: Configuracao teve problemas:" -ForegroundColor Yellow
        Write-Host $response.message -ForegroundColor Yellow
        if ($response.error) {
            Write-Host ""
            Write-Host "Erro:" -ForegroundColor Red
            Write-Host $response.error -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "Configure manualmente no Trendz:" -ForegroundColor Cyan
        Write-Host "   1. Acesse: http://localhost:8888" -ForegroundColor White
        Write-Host "   2. Login: tenant@thingsboard.org / tenant" -ForegroundColor White
        Write-Host "   3. Settings -> Data Sources -> Add PostgreSQL" -ForegroundColor White
        Write-Host "   4. Host: postgres (ou localhost)" -ForegroundColor White
        Write-Host "   5. Port: 5432" -ForegroundColor White
        Write-Host "   6. Database: inmet_db" -ForegroundColor White
        Write-Host "   7. User: inmet_user" -ForegroundColor White
        Write-Host "   8. Password: inmet_password" -ForegroundColor White
    }
} catch {
    Write-Host ""
    Write-Host "ERRO: Erro ao executar configuracao:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Tente executar manualmente:" -ForegroundColor Yellow
    Write-Host "   docker exec -it fastapi-ingestao python /app/scripts/configure_trendz_datasource.py" -ForegroundColor Gray
}

Write-Host ""

