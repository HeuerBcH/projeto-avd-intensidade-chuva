<#
.SYNOPSIS
    Pipeline completo de BI - Classificacao de Intensidade de Chuva
    
.DESCRIPTION
    Script unificado que executa todo o pipeline do projeto em ordem:
    1. Valida pre-requisitos (Docker)
    2. Configura ambiente (.env)
    3. Inicia servicos Docker
    4. Executa scripts SQL
    5. Popula ThingsBoard com dados
    6. Ingere dados para S3 e PostgreSQL
    7. Carrega modelo ML
    8. Exibe URLs de acesso
    
.EXAMPLE
    .\run.ps1
    
.NOTES
    Projeto: Analise e Visualizacao de Dados - 2025.2
    Instituicao: CESAR School
#>

param(
    [switch]$SkipDataLoad,
    [switch]$SkipModelLoad
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERRO] $Message" -ForegroundColor Red
}

function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-Container {
    param([string]$Name)
    $status = docker ps --filter "name=$Name" --format "{{.Status}}" 2>$null
    return $status -ne $null -and $status -ne ""
}

function Wait-ForContainer {
    param(
        [string]$Name,
        [int]$TimeoutSeconds = 60
    )
    
    $elapsed = 0
    while (-not (Test-Container $Name) -and $elapsed -lt $TimeoutSeconds) {
        Start-Sleep -Seconds 2
        $elapsed += 2
    }
    
    return Test-Container $Name
}

function Invoke-SqlScript {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        Write-Error-Custom "Arquivo SQL nao encontrado: $FilePath"
        return $false
    }
    
    try {
        $output = Get-Content $FilePath | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        if ($output -match "ERROR") {
            return $false
        }
        return $true
    } catch {
        return $false
    }
}

function Invoke-ApiEndpoint {
    param(
        [string]$Url,
        [string]$Method = "POST",
        [int]$TimeoutSec = 300
    )
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method $Method -TimeoutSec $TimeoutSec -ErrorAction Stop
        return $response
    } catch {
        Write-Error-Custom "Erro ao chamar $Url : $_"
        return $null
    }
}

Write-Step "PIPELINE INMET - INICIANDO"

Write-Info "Validando pre-requisitos..."
if (-not (Test-Docker)) {
    Write-Error-Custom "Docker nao esta rodando. Inicie o Docker Desktop."
    exit 1
}
Write-Success "Docker esta rodando"

Write-Step "CONFIGURANDO AMBIENTE"

$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Info "Criando arquivo .env..."
    @"
# ========================================
# CONFIGURACOES DO POSTGRESQL
# ========================================
POSTGRES_DB=inmet_db
POSTGRES_USER=inmet_user
POSTGRES_PASSWORD=inmet_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ========================================
# CONFIGURACOES DO MINIO/S3
# ========================================
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=inmet-data

# ========================================
# CONFIGURACOES DO THINGSBOARD
# ========================================
THINGSBOARD_HOST=http://thingsboard:9090
THINGSBOARD_USER=tenant@thingsboard.org
THINGSBOARD_PASSWORD=tenant

# ========================================
# CONFIGURACOES DO JUPYTERLAB
# ========================================
JUPYTER_TOKEN=avd2025

# ========================================
# CONFIGURACOES DO MLFLOW
# ========================================
MLFLOW_TRACKING_URI=http://0.0.0.0:5000
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
"@ | Out-File -FilePath $envFile -Encoding utf8
    Write-Success "Arquivo .env criado"
} else {
    Write-Success "Arquivo .env ja existe"
}

Write-Step "INICIANDO SERVICOS DOCKER"

Write-Info "Subindo containers..."
docker compose up -d

Write-Info "Aguardando PostgreSQL (30s)..."
Start-Sleep -Seconds 30

if (-not (Wait-ForContainer "postgres-inmet" 30)) {
    Write-Error-Custom "PostgreSQL nao iniciou"
    exit 1
}
Write-Success "PostgreSQL pronto"

if (-not (Wait-ForContainer "fastapi-ingestao" 30)) {
    Write-Error-Custom "FastAPI nao iniciou"
    exit 1
}
Write-Success "FastAPI pronto"

if (-not (Wait-ForContainer "thingsboard" 30)) {
    Write-Error-Custom "ThingsBoard nao iniciou"
    exit 1
}
Write-Success "ThingsBoard pronto"

Write-Step "EXECUTANDO SCRIPTS SQL"

$sqlScripts = @(
    "sql_scripts/01_schema.sql",
    "sql_scripts/02_views.sql",
    "sql_scripts/03_update_intensidade_chuva.sql",
    "sql_scripts/04_views_trendz.sql"
)

foreach ($script in $sqlScripts) {
    Write-Info "Executando $script..."
    if (Invoke-SqlScript $script) {
        Write-Success "$script executado"
    } else {
        Write-Error-Custom "Falha ao executar $script"
    }
}

if (-not $SkipDataLoad) {
    Write-Step "CARREGANDO DADOS"
    
    Write-Info "Populando ThingsBoard..."
    $response = Invoke-ApiEndpoint "http://localhost:8000/populate-thingsboard"
    if ($response) {
        Write-Success "ThingsBoard populado"
    }
    
    Write-Info "Ingerindo dados para S3 e PostgreSQL (pode demorar)..."
    $response = Invoke-ApiEndpoint "http://localhost:8000/ingest-from-thingsboard" -TimeoutSec 600
    if ($response) {
        Write-Success "Dados ingeridos"
    }
} else {
    Write-Info "Carregamento de dados ignorado (use sem -SkipDataLoad para carregar)"
}

if (-not $SkipModelLoad) {
    Write-Step "CARREGANDO MODELO ML"
    
    Write-Info "Verificando modelos disponiveis..."
    $models = Invoke-ApiEndpoint "http://localhost:8000/models" -Method "GET"
    
    if ($models) {
        Write-Info "Carregando melhor modelo..."
        $response = Invoke-ApiEndpoint "http://localhost:8000/models/load"
        if ($response) {
            Write-Success "Modelo ML carregado"
        } else {
            Write-Info "Execute os notebooks 02 e 03 no JupyterLab para treinar o modelo"
        }
    }
} else {
    Write-Info "Carregamento de modelo ignorado (use sem -SkipModelLoad para carregar)"
}

Write-Step "PIPELINE CONCLUIDO"

Write-Host "`n[SERVICOS DISPONIVEIS]`n" -ForegroundColor Green
Write-Host "  FastAPI:        http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ThingsBoard:    http://localhost:9090" -ForegroundColor White
Write-Host "                  (tenant@thingsboard.org / tenant)" -ForegroundColor Gray
Write-Host "  JupyterLab:     http://localhost:1010" -ForegroundColor White
Write-Host "                  (token: avd2025)" -ForegroundColor Gray
Write-Host "  MLFlow:         http://localhost:5000" -ForegroundColor White
Write-Host "  MinIO Console:  http://localhost:9001" -ForegroundColor White
Write-Host "                  (minioadmin / minioadmin)" -ForegroundColor Gray
Write-Host "  PostgreSQL:     localhost:5432" -ForegroundColor White
Write-Host "                  (inmet_user / inmet_password)" -ForegroundColor Gray

Write-Host "`n[PROXIMOS PASSOS]`n" -ForegroundColor Cyan
Write-Host "  1. Execute os notebooks no JupyterLab:" -ForegroundColor White
Write-Host "     - 02_tratamento_limpeza.ipynb (classificar intensidade)" -ForegroundColor Gray
Write-Host "     - 03_modelagem_mlflow.ipynb (treinar modelo)" -ForegroundColor Gray
Write-Host "`n  2. Recarregue o modelo:" -ForegroundColor White
Write-Host "     curl.exe -X POST http://localhost:8000/models/load" -ForegroundColor Gray
Write-Host "`n  3. Faca predicoes:" -ForegroundColor White
Write-Host "     curl.exe -X POST http://localhost:8000/trendz/predict -H `"Content-Type: application/json`" -d '{...}'" -ForegroundColor Gray

Write-Host "`n[COMANDOS UTEIS]`n" -ForegroundColor Yellow
Write-Host "  Ver logs:       docker compose logs -f" -ForegroundColor Gray
Write-Host "  Parar tudo:     docker compose down" -ForegroundColor Gray
Write-Host "  Reiniciar:      docker compose restart" -ForegroundColor Gray

Write-Host ""
