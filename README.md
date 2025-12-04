# Projeto AVD - Classificacao de Intensidade de Chuva

Pipeline completo de BI para classificacao de intensidade de chuva usando dados do INMET.

## Inicio Rapido

### 1. Configurar Credenciais

```powershell
# Copiar template
Copy-Item .env.example .env

# Editar com suas credenciais (ou usar padroes)
notepad .env
```

### 2. Executar Pipeline

```powershell
.\run.ps1
```

O script automaticamente:
- Valida Docker
- Cria .env se nao existir (com valores padrao)
- Inicia todos os servicos
- Executa scripts SQL
- Popula ThingsBoard
- Ingere dados para S3/PostgreSQL
- Carrega modelo ML

## Servicos Disponiveis

Apos executar `.\run.ps1`, acesse:

- **FastAPI:** http://localhost:8000/docs
- **ThingsBoard:** http://localhost:9090 (tenant@thingsboard.org / tenant)
- **JupyterLab:** http://localhost:1010 (token: avd2025)
- **MLFlow:** http://localhost:5000
- **MinIO Console:** http://localhost:9001 (minioadmin / minioadmin)
- **PostgreSQL:** localhost:5432 (inmet_user / inmet_password)

## Estrutura do Projeto

```
projeto-avd-intensidade-chuva/
├── .env                        # Credenciais (NAO commitado)
├── .env.example                # Template de credenciais
├── docker-compose.yml          # Orquestracao de servicos
├── run.ps1                     # Script unificado de execucao
├── COMO_EXECUTAR.md            # Guia de execucao
├── MIGRACAO_ENV.md             # Guia de migracao do .env
├── fastapi/                    # API de ingestao
│   └── app/
│       ├── services/           # Servicos (S3, DB, ThingsBoard, MLFlow)
│       └── scripts/            # Scripts auxiliares
├── notebooks/                  # Notebooks Jupyter
│   ├── 02_tratamento_limpeza.ipynb
│   └── 03_modelagem_mlflow.ipynb
├── sql_scripts/                # Scripts SQL
│   ├── 01_schema.sql
│   ├── 02_views.sql
│   ├── 03_update_intensidade_chuva.sql
│   └── 04_views_trendz.sql
└── data/                       # Dados (nao versionados)
    ├── postgres/
    └── minio/
```

## Configuracao

### Arquivo .env (na raiz)

O projeto usa UM UNICO arquivo `.env` na raiz com todas as configuracoes:

```env
# PostgreSQL
POSTGRES_DB=inmet_db
POSTGRES_USER=inmet_user
POSTGRES_PASSWORD=inmet_password

# MinIO (S3-compatible LOCAL - NAO usa AWS)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET_NAME=inmet-data

# ThingsBoard
THINGSBOARD_USER=tenant@thingsboard.org
THINGSBOARD_PASSWORD=tenant

# JupyterLab
JUPYTER_TOKEN=avd2025

# MLFlow (usa MinIO como storage)
MLFLOW_TRACKING_URI=http://0.0.0.0:5000
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
```

**NOTA:** As variaveis `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` sao usadas pelo MinIO (compatibilidade S3), nao pela AWS.

**IMPORTANTE:** O `.env` deve estar na RAIZ do projeto, nao em `fastapi/app/.env`

## Workflow

### 1. Ingestao de Dados

```powershell
# Popular ThingsBoard
curl.exe -X POST http://localhost:8000/populate-thingsboard

# Ingerir para S3 e PostgreSQL
curl.exe -X POST http://localhost:8000/ingest-from-thingsboard
```

### 2. Analise e Modelagem

Acesse JupyterLab (http://localhost:1010) e execute:

1. `02_tratamento_limpeza.ipynb` - Classificar intensidade de chuva
2. `03_modelagem_mlflow.ipynb` - Treinar modelo ML

### 3. Carregar Modelo

```powershell
curl.exe -X POST http://localhost:8000/models/load
```

### 4. Fazer Predicoes

```powershell
curl.exe -X POST http://localhost:8000/trendz/predict -H "Content-Type: application/json" -d '{
  "temperatura_ar_c": 25.5,
  "umidade_rel_horaria_pct": 80.0,
  "pressao_estacao_mb": 1013.25,
  "vento_velocidade_ms": 3.5
}'
```

## Comandos Uteis

```powershell
# Ver logs
docker compose logs -f

# Parar servicos
docker compose down

# Reiniciar servicos
docker compose restart

# Limpar tudo (CUIDADO: apaga dados)
docker compose down -v
```

## Troubleshooting

### Erro: "Docker nao esta rodando"
Inicie o Docker Desktop

### Erro: "password authentication failed"
Verifique credenciais no `.env`:
```env
POSTGRES_USER=inmet_user
POSTGRES_PASSWORD=inmet_password
```

### Erro: "No such file: .env"
```powershell
Copy-Item .env.example .env
notepad .env
```

### Modelo nao encontrado
Execute os notebooks 02 e 03 no JupyterLab primeiro

## Conectar pgAdmin

Use estas credenciais:

- Host: `localhost`
- Port: `5432`
- Database: `inmet_db`
- Username: `inmet_user`
- Password: `inmet_password`

## Tecnologias

- **FastAPI** - API de ingestao
- **PostgreSQL** - Banco de dados estruturado
- **MinIO** - Armazenamento S3 local
- **ThingsBoard** - Plataforma IoT
- **JupyterLab** - Analise de dados
- **MLFlow** - Gerenciamento de modelos ML
- **Docker** - Containerizacao

**IMPORTANTE:** Este projeto usa MinIO como storage local compativel com S3. NAO usa AWS S3.

## Documentacao

- `COMO_EXECUTAR.md` - Guia completo de execucao
- `MIGRACAO_ENV.md` - Guia de migracao do .env para a raiz

## Licenca

MIT License

## Contato

Projeto desenvolvido para a disciplina **Analise e Visualizacao de Dados - 2025.2**  
**CESAR School**
