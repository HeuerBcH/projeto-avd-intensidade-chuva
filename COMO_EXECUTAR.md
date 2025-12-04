# Como Executar o Projeto

## Pre-requisitos

- Windows 10/11
- Docker Desktop instalado e rodando
- PowerShell 5.1 ou superior

## Passo 1: Configurar Credenciais

Antes de executar, configure o arquivo `.env` na raiz:

```powershell
# Copiar template
Copy-Item .env.example .env

# Editar com as credenciais corretas (veja CONFIGURACAO.md)
notepad .env
```

**Credenciais padrao do projeto:**
- PostgreSQL: `inmet_user` / `inmet_password`
- MinIO: `minioadmin` / `minioadmin`
- ThingsBoard: `tenant@thingsboard.org` / `tenant`
- JupyterLab: token `avd2025`

Veja detalhes completos em `CONFIGURACAO.md`

## Passo 2: Executar Pipeline

```powershell
.\run.ps1
```

## O que o script faz

1. **Valida Docker** - Verifica se está rodando
2. **Configura ambiente** - Cria arquivo `.env` automaticamente
3. **Inicia serviços** - Sobe todos os containers Docker
4. **Executa SQL** - Cria schema, views e tabelas
5. **Carrega dados** - Popula ThingsBoard e ingere para S3/PostgreSQL
6. **Carrega modelo** - Tenta carregar modelo ML (se disponível)

## Opções Avançadas

```powershell
.\run.ps1 -SkipDataLoad      # Pula carregamento de dados (mais rápido)
.\run.ps1 -SkipModelLoad     # Pula carregamento de modelo
```

## Após Execução

### 1. Treinar Modelo ML

Acesse: http://localhost:1010 (token: `avd2025`)

Execute em ordem:
1. `notebooks/02_tratamento_limpeza.ipynb`
2. `notebooks/03_modelagem_mlflow.ipynb`

### 2. Recarregar Modelo

```powershell
curl.exe -X POST http://localhost:8000/models/load
```

### 3. Acessar Dashboards

- **FastAPI:** http://localhost:8000/docs
- **MLFlow:** http://localhost:5000
- **ThingsBoard:** http://localhost:9090
- **JupyterLab:** http://localhost:1010

## Parar Serviços

```powershell
docker compose down
```

## Troubleshooting

### Erro: "password authentication failed"
**Causa:** Credenciais incorretas no `.env`

**Solucao:** Edite `.env` na raiz e use:
```env
POSTGRES_USER=inmet_user
POSTGRES_PASSWORD=inmet_password
```

Depois reinicie:
```powershell
docker compose restart
```

### Erro: "Docker nao esta rodando"
Abra o Docker Desktop e aguarde inicializar

### Erro: "Container nao iniciou"
Aguarde 60 segundos e tente novamente. Verifique logs:
```powershell
docker compose logs [nome-do-servico]
```

### Erro: "Modelo nao encontrado"
Execute os notebooks 02 e 03 no JupyterLab primeiro

### Erro: "No such file: .env"
Configure o arquivo `.env` primeiro (veja Passo 1)

## Tempo Estimado

- **Primeira execução:** ~5-10 minutos (com carregamento de dados)
- **Execuções seguintes:** ~2-3 minutos (com `-SkipDataLoad`)
