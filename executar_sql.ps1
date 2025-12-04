# Script PowerShell para executar arquivos SQL no PostgreSQL
# Uso: .\executar_sql.ps1 [arquivo.sql]

param(
    [string]$arquivo = "sql_scripts/04_views_grafana.sql",
    [string]$container = "postgres-inmet",
    [string]$usuario = "inmet_user",
    [string]$database = "inmet_db"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Executando Script SQL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $arquivo)) {
    Write-Host "❌ Arquivo não encontrado: $arquivo" -ForegroundColor Red
    exit 1
}

Write-Host "📄 Arquivo: $arquivo" -ForegroundColor Yellow
Write-Host "🐳 Container: $container" -ForegroundColor Yellow
Write-Host "💾 Database: $database" -ForegroundColor Yellow
Write-Host ""

Write-Host "Executando script..." -ForegroundColor Cyan

# Executa o script SQL
Get-Content $arquivo | docker exec -i $container psql -U $usuario -d $database

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Script executado com sucesso!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Erro ao executar script (código: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

