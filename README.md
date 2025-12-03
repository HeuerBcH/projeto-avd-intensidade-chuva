# 🌧️ Pipeline de BI - Classificação de Intensidade de Chuva

Pipeline completo de Business Intelligence para análise e classificação de intensidade de precipitação usando dados do INMET.

## 📋 Estrutura do Projeto

```
projeto-avd-intensidade-chuva/
├── docker-compose.yml          # Orquestração dos serviços
├── fastapi/                    # API de ingestão de dados
├── notebooks/                  # Análise e modelagem ML
├── sql_scripts/                # Scripts SQL (schema, views)
├── mlflow/                     # Experimentos e modelos ML
├── trendz/                     # Dashboards Trendz Analytics
└── data/                       # Dados (PostgreSQL, MinIO)
```

## 🚀 Início Rápido

### 1. Subir os Serviços

```powershell
docker-compose up -d
```

### 2. Executar Scripts SQL

**⚠️ IMPORTANTE: No PowerShell, use um destes comandos:**

**Opção 1: Script PowerShell (Recomendado)**
```powershell
.\executar_sql.ps1 sql_scripts/04_views_trendz.sql
```

**Opção 2: Comando direto PowerShell**
```powershell
Get-Content sql_scripts/04_views_trendz.sql | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db
```

**Opção 3: Script Batch**
```powershell
.\executar_sql.bat sql_scripts/04_views_trendz.sql
```

**❌ NÃO USE (não funciona no PowerShell):**
```powershell
docker exec -i postgres-inmet psql -U inmet_user -d inmet_db < sql_scripts/04_views_trendz.sql
```

### 3. Carregar Dados

```powershell
# Popular ThingsBoard com dados
curl.exe -X POST http://localhost:8000/populate-thingsboard

# Ingerir dados do ThingsBoard para S3 e PostgreSQL
curl.exe -X POST http://localhost:8000/ingest-from-thingsboard
```

### 4. Classificar Intensidade de Chuva (OBRIGATÓRIO)

**⚠️ IMPORTANTE:** Antes de treinar o modelo, você precisa classificar a intensidade de chuva nos dados.

1. Acesse JupyterLab: http://localhost:1010 (token: `avd2025`)
2. Execute o notebook: `notebooks/02_tratamento_limpeza.ipynb`
3. Isso vai classificar a intensidade de chuva nos dados

### 5. Treinar Modelo ML (OBRIGATÓRIO)

1. No JupyterLab, execute: `notebooks/03_modelagem_mlflow.ipynb`
2. Isso vai treinar e salvar modelos no MLFlow

### 6. Carregar Modelo ML

```powershell
# Verificar modelos disponíveis
curl.exe -X GET http://localhost:8000/models

# Carregar melhor modelo
curl.exe -X POST http://localhost:8000/models/load
```

**⚠️ Se retornar "Modelo não encontrado":**
- Execute primeiro os notebooks 02 e 03 (veja `PASSO_A_PASSO_MODELO.md`)

### 5. Acessar Serviços

- **FastAPI:** http://localhost:8000/docs
- **MLFlow:** http://localhost:5000
- **Trendz Analytics:** http://localhost:8888
- **ThingsBoard:** http://localhost:9090
- **JupyterLab:** http://localhost:1010 (token: `avd2025`)
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

## 🔧 Configuração do Trendz

### ⚠️ IMPORTANTE: Configuração Manual Necessária

O Trendz Analytics **NÃO possui API pública** para criar datasources. Você precisa configurar **MANUALMENTE** através da interface web.

### 📋 Guia Completo de Configuração Manual

Siga o guia passo a passo: [`trendz/COMO_CONFIGURAR_DATASOURCE.md`](trendz/COMO_CONFIGURAR_DATASOURCE.md)

### 🚀 Resumo Rápido:

1. Acesse: http://localhost:8888
2. Login: `tenant@thingsboard.org` / `tenant`
3. Vá em **Settings** → **Data Sources** (ou procure no menu)
4. Clique em **Add new data source**
5. Preencha os **3 campos obrigatórios**:
   - **URL***: `jdbc:postgresql://postgres:5432/inmet_db`
     - (Use `jdbc:postgresql://localhost:5432/inmet_db` se acessando do host Windows)
   - **Login***: `inmet_user`
   - **Password***: `inmet_password`
6. Clique em **Save** (botão no canto inferior direito)

### 📊 Queries SQL Prontas

Se não conseguir configurar datasource, use queries SQL direto nos widgets:
[`trendz/QUERIES_SQL_PARA_WIDGETS.md`](trendz/QUERIES_SQL_PARA_WIDGETS.md)

**Resumo Rápido:**

1. Acesse http://localhost:8888
2. Login: `tenant@thingsboard.org` / `tenant`
3. Configure datasource PostgreSQL:
   - Host: `postgres` (ou `localhost` do host)
   - Port: `5432`
   - Database: `inmet_db`
   - User: `inmet_user`
   - Password: `inmet_password`
4. Use as views SQL criadas para criar widgets

## 📊 Endpoints Principais

### FastAPI

- `GET /` - Lista de endpoints
- `POST /ingest-from-thingsboard` - Coleta dados do ThingsBoard
- `POST /trendz/predict` - Predição otimizada para Trendz
- `POST /trendz/predict-from-db` - Predições em lote
- `POST /configure-trendz` - Configura datasource PostgreSQL automaticamente
- `GET /models` - Lista modelos disponíveis
- `POST /models/load` - Carrega melhor modelo

### Exemplo de Predição

```powershell
curl.exe -X POST http://localhost:8000/trendz/predict `
  -H "Content-Type: application/json" `
  -d '{\"codigo_wmo\": \"A307\", \"precipitacao_mm\": 5.2, \"pressao_estacao_mb\": 1013.5, \"temperatura_ar_c\": 25.3, \"umidade_rel_horaria_pct\": 75.0, \"vento_velocidade_ms\": 3.5}'
```

## 📚 Documentação

- [`trendz/GUIA_COMPLETO.md`](trendz/GUIA_COMPLETO.md) - Guia completo do Trendz
- [`RESOLUCAO_TRENDZ.md`](RESOLUCAO_TRENDZ.md) - Resolução da integração Trendz
- [`COMANDOS_POWERSHELL.md`](COMANDOS_POWERSHELL.md) - Comandos PowerShell
- [`ANALISE_E_PLANO.md`](ANALISE_E_PLANO.md) - Análise e plano do projeto

## 🐳 Serviços Docker

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| FastAPI | 8000 | API de ingestão |
| PostgreSQL | 5432 | Banco de dados |
| MinIO | 9000/9001 | Armazenamento S3 |
| MLFlow | 5000 | Tracking de ML |
| Trendz | 8888 | Dashboards |
| ThingsBoard | 9090 | Plataforma IoT |
| JupyterLab | 1010 | Notebooks |

## 🔑 Credenciais Padrão

- **PostgreSQL:** `inmet_user` / `inmet_password`
- **MinIO:** `minioadmin` / `minioadmin`
- **ThingsBoard/Trendz:** `tenant@thingsboard.org` / `tenant`
- **JupyterLab:** Token: `avd2025`

## 📝 Notas Importantes

1. **PowerShell:** Use `Get-Content` ou os scripts fornecidos para executar SQL
2. **Modelo ML:** Carregue o modelo antes de fazer predições (`/models/load`)
3. **Trendz:** Configure o datasource PostgreSQL antes de criar dashboards
4. **Dados:** Execute `/populate-thingsboard` antes de `/ingest-from-thingsboard`

## 🛠️ Troubleshooting

### Erro ao executar SQL no PowerShell

**Erro:** `Operador '<' reservado para uso futuro`

**Solução:** Use um dos comandos corretos listados acima (Opções 1, 2 ou 3)

### Trendz não conecta ao ThingsBoard

Verifique se o ThingsBoard está rodando:
```powershell
docker ps | Select-String thingsboard
```

### Modelo não encontrado

Execute o notebook `03_modelagem_mlflow.ipynb` para treinar e salvar o modelo.

## 📧 Contato

Projeto desenvolvido para a disciplina **Análise e Visualização de Dados - 2025.2**  
**CESAR School**
