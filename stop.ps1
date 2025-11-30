# Script PowerShell para parar todos os serviços
Write-Host "Parando containers Docker..." -ForegroundColor Yellow
docker compose down
Write-Host "Serviços parados!" -ForegroundColor Green

