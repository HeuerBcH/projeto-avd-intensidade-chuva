Write-Host ""
Write-Host "🛑 Parando serviços do pipeline..." -ForegroundColor Yellow
Write-Host ""

docker compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Serviços parados com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Para iniciar novamente, execute: .\start.ps1" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "⚠️  Alguns serviços podem não ter sido parados corretamente." -ForegroundColor Yellow
}

Write-Host ""
