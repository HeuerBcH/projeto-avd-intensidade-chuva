# 🌧️ Pipeline de BI - Classificação de Intensidade de Chuva

[![Docker](https://img.shields.io/badge/Docker-Required-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Pipeline completo de Business Intelligence para análise e classificação automática de intensidade de precipitação utilizando dados meteorológicos do INMET (Instituto Nacional de Meteorologia).

**Disciplina:** Análise e Visualização de Dados - 2025.2  
**Instituição:** CESAR School  
**Problema:** 7.8 - Classificar Intensidade da Chuva
**Integrantes** - Bernardo Heuer (@HeuerBcH), Erick Belo, Eduardo Roma, Leonardo Méllo (@Leonardo-Mello22), Vinicius Beltrão, Rodrigo Nunes (@rodrigonuness), Silvio Fittipaldi (@SilvioFittipald1).

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Serviços](#-serviços)
- [Documentação](#-documentação)
- [Troubleshooting](#-troubleshooting)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🎯 Sobre o Projeto

Este projeto implementa um pipeline completo de Business Intelligence para análise de dados meteorológicos, com foco na classificação automática de intensidade de precipitação. O sistema integra coleta de dados, armazenamento, processamento, modelagem de machine learning e visualização interativa.

### Objetivos

- ✅ Coletar e processar dados meteorológicos do INMET
- ✅ Classificar automaticamente a intensidade de chuva em 4 categorias
- ✅ Treinar e versionar modelos de machine learning
- ✅ Visualizar dados e resultados em dashboards interativos
- ✅ Fornecer API para predições em tempo real

### Classificação de Intensidade

O sistema classifica a precipitação em quatro categorias:

| Categoria | Limiar | Descrição |
|-----------|--------|-----------|
| **Sem chuva** | 0 mm | Ausência de precipitação |
| **Leve** | 0.1 - 2.5 mm/h | Chuva fraca |
| **Moderada** | 2.6 - 10 mm/h | Chuva moderada |
| **Forte** | > 10 mm/h | Chuva intensa |

---

## ✨ Características

- 🐳 **Containerizado**: Toda a infraestrutura em Docker Compose
- 🚀 **Setup Automático**: Script de inicialização que configura tudo
- 📊 **Dashboards Interativos**: Grafana com 20+ visualizações prontas
- 🤖 **Machine Learning**: Modelos treinados e versionados com MLFlow
- 🔄 **Pipeline Completo**: Da coleta à visualização
- 📈 **Análise Temporal**: Visualizações de séries temporais
- 🎨 **Visualizações Diversas**: Barras, linhas, heatmaps, tabelas, etc.
- 🔌 **API REST**: Endpoints para ingestão e predição

---

## 🏗️ Arquitetura

```
┌─────────────┐
│   CSVs      │
│  (INMET)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│ ThingsBoard │────▶│   FastAPI    │
│  (IoT)      │     │  (Ingestão)  │
└─────────────┘     └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌────────────┐  ┌──────────┐
    │  MinIO   │    │ PostgreSQL │  │ Jupyter  │
    │   (S3)   │    │   (BD)     │  │ Notebooks│
    └──────────┘    └──────┬─────┘  └─────┬────┘
                           │              │
                           ▼              ▼
                    ┌────────────┐  ┌──────────┐
                    │   MLFlow   │  │ Grafana  │
                    │  (ML Ops)  │  │(Viz)     │
                    └────────────┘  └──────────┘
```

### Fluxo de Dados

1. **Coleta**: Arquivos CSV do INMET são processados
2. **Ingestão**: FastAPI coleta dados e armazena em MinIO e PostgreSQL
3. **Tratamento**: Notebooks Jupyter processam e classificam dados
4. **Modelagem**: Modelos ML são treinados e versionados no MLFlow
5. **Visualização**: Grafana consome dados do PostgreSQL
6. **Predição**: API permite predições em tempo real

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop))
- **Git** ([Download](https://git-scm.com/downloads))
- **PowerShell** (Windows) ou **Bash** (Linux/Mac)
- **~5GB** de espaço em disco livre

---

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone <url-do-repositorio>
cd projeto-avd-intensidade-chuva
```

### 2. Execute o Script de Inicialização

**Windows:**
```powershell
.\start.ps1
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

O script irá automaticamente:
- ✅ Verificar se o Docker está rodando
- ✅ Criar estrutura de diretórios
- ✅ Criar arquivo `.env` com configurações
- ✅ Subir todos os containers Docker
- ✅ Aguardar serviços ficarem prontos

**⏱️ Tempo estimado:** 2-3 minutos na primeira execução

### 3. Adicione Dados CSV (Opcional)

Coloque os arquivos CSV do INMET em:
```
fastapi/app/data/raw/
```

---

## 💻 Uso

### Iniciar o Pipeline

Após executar `start.ps1`, todos os serviços estarão disponíveis:

| Serviço | URL | Credenciais |
|---------|-----|------------|
| **FastAPI** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3000 | `admin` / `admin` |
| **JupyterLab** | http://localhost:1010 | Token: `avd2025` |
| **MLFlow** | http://localhost:5000 | - |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin` |
| **ThingsBoard** | http://localhost:9090 | `tenant@thingsboard.org` / `tenant` |

### Fluxo de Trabalho Completo

#### 1. Ingerir Dados

**Opção A: Via ThingsBoard (Recomendado)**
```powershell
# Popular ThingsBoard com dados históricos
curl.exe -X POST http://localhost:8000/populate-thingsboard

# Ingerir dados do ThingsBoard para S3 e PostgreSQL
curl.exe -X POST http://localhost:8000/ingest-from-thingsboard
```

**Opção B: Direto no Banco**
```powershell
curl.exe -X POST http://localhost:8000/load-to-db
```

#### 2. Classificar Intensidade de Chuva

**Via Jupyter Notebook:**
1. Acesse: http://localhost:1010
2. Execute: `notebooks/02_tratamento_limpeza.ipynb`

**Via SQL:**
```powershell
.\executar_sql.ps1 sql_scripts/03_update_intensidade_chuva.sql
```

#### 3. Criar Views para Grafana

```powershell
.\executar_sql.ps1 sql_scripts/04_views_grafana.sql
```

#### 4. Treinar Modelos ML

1. Acesse JupyterLab: http://localhost:1010
2. Execute: `notebooks/03_modelagem_mlflow.ipynb`

#### 5. Visualizar no Grafana

1. Acesse: http://localhost:3000
2. Login: `admin` / `admin`
3. Dashboard: **"Classificação de Intensidade de Chuva - INMET"**

### Executar Notebooks

Execute os notebooks na seguinte ordem:

1. **01_eda_exploracao.ipynb** - Análise exploratória dos dados
2. **02_tratamento_limpeza.ipynb** - Tratamento e classificação ⚠️ **OBRIGATÓRIO**
3. **03_modelagem_mlflow.ipynb** - Treinamento de modelos ⚠️ **OBRIGATÓRIO**
4. **04_preparacao_visualizacao.ipynb** - Preparação de dados para visualização
5. **05_visualizacoes_finais.ipynb** - Visualizações finais e análises

### Endpoints da API

#### Ingestão de Dados
- `GET /` - Lista de endpoints disponíveis
- `POST /populate-thingsboard` - Popula ThingsBoard com dados históricos
- `POST /ingest-from-thingsboard` - Ingestão de dados do ThingsBoard
- `POST /load-to-db` - Carrega CSVs diretamente no PostgreSQL
- `GET /stats` - Estatísticas do banco de dados

#### Testes de Conexão
- `GET /test-connection` - Testa conexão com MinIO/S3
- `GET /test-db` - Testa conexão com PostgreSQL
- `GET /test-thingsboard` - Testa conexão com ThingsBoard

#### Machine Learning
- `GET /models` - Lista modelos disponíveis no MLFlow
- `POST /models/load` - Carrega melhor modelo
- `GET /models/info` - Informações do modelo carregado
- `POST /predict` - Predição de intensidade de chuva
- `POST /predict-from-db` - Predições em lote a partir do banco

#### Exemplo de Predição

```powershell
curl.exe -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d '{
    "precipitacao_mm": 5.2,
    "pressao_estacao_mb": 1013.5,
    "temperatura_ar_c": 25.3,
    "umidade_rel_horaria_pct": 75.0,
    "vento_velocidade_ms": 3.5
  }'
```

---

## 📁 Estrutura do Projeto

```
projeto-avd-intensidade-chuva/
├── docker-compose.yml              # Orquestração dos serviços
├── start.ps1 / start.sh            # Scripts de inicialização
├── stop.ps1 / stop.sh              # Scripts para parar serviços
├── executar_sql.ps1                # Script para executar SQL
│
├── fastapi/                        # API de ingestão de dados
│   └── app/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── services/               # Serviços principais
│       │   ├── main.py            # Aplicação FastAPI
│       │   ├── data_loader.py
│       │   ├── csv_processor.py
│       │   ├── s3_service.py
│       │   ├── db_service.py
│       │   ├── thingsboard_service.py
│       │   └── mlflow_service.py
│       ├── scripts/               # Scripts de inicialização
│       │   ├── init_pipeline.py
│       │   └── populate_thingsboard.py
│       └── data/raw/              # Coloque arquivos CSV aqui
│
├── notebooks/                      # Análise e modelagem ML
│   ├── 01_eda_exploracao.ipynb
│   ├── 02_tratamento_limpeza.ipynb
│   ├── 03_modelagem_mlflow.ipynb
│   ├── 04_preparacao_visualizacao.ipynb
│   └── 05_visualizacoes_finais.ipynb
│
├── sql_scripts/                    # Scripts SQL
│   ├── 00_init_databases.sql      # Cria banco ThingsBoard
│   ├── 01_schema.sql              # Schema principal
│   ├── 02_views.sql               # Views auxiliares
│   ├── 03_update_intensidade_chuva.sql  # Classificação
│   └── 04_views_grafana.sql       # Views para Grafana
│
├── grafana/                        # Configuração Grafana
│   ├── provisioning/
│   │   ├── datasources/          # PostgreSQL configurado
│   │   │   └── postgres.yml
│   │   └── dashboards/           # Dashboard provisionado
│   │       ├── dashboard.yml
│   │       └── intensidade-chuva.json
│   └── queries_sql_completas.md   # 20 queries SQL prontas
│
├── jupyterlab/                     # Dockerfile JupyterLab
│   └── Dockerfile
│
├── mlflow/                         # Dados do MLFlow (não versionado)
│   └── .gitkeep
│
├── data/                           # Dados (não versionado)
│   ├── postgres/                  # Dados PostgreSQL
│   ├── minio/                     # Dados MinIO
│   └── raw/                       # CSVs brutos
│
├── thingsboard/                    # Dados ThingsBoard (não versionado)
│   └── .gitkeep
│
├── .gitignore                      # Arquivos ignorados pelo Git
├── LICENSE                         # Licença do projeto
└── README.md                       # Este arquivo
```

---

## 🔧 Serviços

### FastAPI (Porta 8000)
API REST para ingestão de dados, consultas e predições.

**Documentação:** http://localhost:8000/docs

### Grafana (Porta 3000)
Dashboards interativos para visualização de dados.

**Login:** `admin` / `admin`

**Dashboard Provisionado:** "Classificação de Intensidade de Chuva - INMET"

**Plugins instalados automaticamente:**

- Nenhum plugin adicional é necessário para o dashboard principal de intensidade de chuva. Ele foi implementado apenas com **painéis nativos** do Grafana (`barchart` e `timeseries`).

> Observação: o arquivo `backup-do-dashboard-grafana.json` é um **dashboard exportado diretamente do Grafana**, mantido apenas como referência das configurações visuais finais e para auxílio na correção. Ele foi criado depois de terminarmos a configuração dos graficos pelo Grafana, exportando o código com todas as configurações extras adicionadas direto no Grafana. Está na raiz do nosso projeto, unicamente para análise do professor, só se torna útil se for importado ao Grafana quando o projeto rodas, podendo analisar ele visualmente.

### Interações no dashboard de intensidade de chuva

- **Seleção de estação:** use os filtros no topo do dashboard (`UF` e `Estação`) para escolher uma ou mais estações.
- **Seleção de intensidade:** o filtro `Intensidade` permite focar em uma ou mais classes (leve, moderada, forte).
- **Gráficos disponíveis:**
  - Gráfico de barras com a **distribuição de intensidade de chuva** (leve, moderada, forte), excluindo explicitamente a classe `sem_chuva`.
  - Quatro gráficos de barras nativos mostrando, por classe de intensidade, a **precipitação média (mm)**, **pressão média (hPa)**, **umidade relativa média (%)** e **velocidade média do vento (m/s)**.
  - Quatro gráficos de séries temporais nativos para as mesmas métricas, com dados agregados em janelas de **30 minutos (média)** para reduzir a densidade de pontos e facilitar a análise.
  - Eixos Y configurados com unidades e faixas adequadas (por exemplo, umidade de 0–100%, pressão de 800–1200 hPa, vento até 4 m/s).

### Backup do Grafana

<!-- Seção a ser preenchida -->

### JupyterLab (Porta 1010)
Ambiente de análise e modelagem com notebooks.

**Token:** `avd2025`

### MLFlow (Porta 5000)
Tracking de experimentos e versionamento de modelos ML.

### PostgreSQL (Porta 5432)
Banco de dados relacional para dados estruturados.

**Credenciais:** `inmet_user` / `inmet_password`

### MinIO (Portas 9000/9001)
Armazenamento de objetos compatível com S3.

**Console:** http://localhost:9001  
**Credenciais:** `minioadmin` / `minioadmin`

### ThingsBoard (Porta 9090)
Plataforma IoT para simulação de dispositivos.

**Login:** `tenant@thingsboard.org` / `tenant`

---

## 📚 Documentação

### Documentação Adicional

- **Queries SQL para Grafana:** [`grafana/queries_sql_completas.md`](grafana/queries_sql_completas.md)
  - 20 queries SQL prontas para uso
  - Visualizações interativas
  - Exemplos de configuração

### Estrutura do Banco de Dados

#### Tabelas Principais

- **`estacoes`**: Metadados das estações meteorológicas
- **`dados_meteorologicos`**: Dados meteorológicos horários
  - Inclui coluna `intensidade_chuva` (sem_chuva, leve, moderada, forte)

#### Views para Grafana

Execute `sql_scripts/04_views_grafana.sql` para criar as views:

- `vw_grafico_barras_intensidade` - Gráfico de barras por classe
- `vw_temporal_diaria_intensidade` - Linha temporal diária
- `vw_estatisticas_por_estacao` - Estatísticas por estação
- `vw_distribuicao_intensidade_estacao` - Distribuição por estação
- `vw_resumo_geral` - Resumo geral (cards/métricas)
- E mais...

---

## 🛠️ Comandos Úteis

```powershell
# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f fastapi

# Parar todos os serviços
.\stop.ps1

# Reiniciar serviços
docker compose restart

# Verificar status dos containers
docker compose ps

# Executar SQL
.\executar_sql.ps1 sql_scripts/04_views_grafana.sql

# Acessar shell do container
docker exec -it fastapi-ingestao bash
```

---

## 🆘 Troubleshooting

### Docker não está rodando
- Inicie o Docker Desktop
- Aguarde até que esteja totalmente iniciado
- Verifique: `docker info`

### Erro ao iniciar containers
- Verifique se as portas estão livres:
  - 8000 (FastAPI)
  - 3000 (Grafana)
  - 5000 (MLFlow)
  - 9090 (ThingsBoard)
  - 1010 (JupyterLab)
  - 5432 (PostgreSQL no Docker - pode ser alterado no `docker-compose.yml`)
- Execute: `docker compose down` e depois `.\start.ps1`

### FastAPI não responde
- Aguarde alguns minutos após iniciar
- Verifique logs: `docker compose logs fastapi`
- Verifique se o container está rodando: `docker compose ps`

### Sem dados no Grafana
1. Verifique se os dados foram carregados:
   ```powershell
   curl.exe http://localhost:8000/stats
   ```
2. Execute a classificação de intensidade:
   ```powershell
   .\executar_sql.ps1 sql_scripts/03_update_intensidade_chuva.sql
   ```
3. Execute as views SQL:
   ```powershell
   .\executar_sql.ps1 sql_scripts/04_views_grafana.sql
   ```

### Modelo não encontrado
- Execute o notebook `03_modelagem_mlflow.ipynb` primeiro
- Verifique se o MLFlow está rodando: http://localhost:5000
- Carregue o modelo: `POST http://localhost:8000/models/load`

### Erro ao executar SQL no PowerShell
**Erro:** `Operador '<' reservado para uso futuro`

**Solução:** Use o script fornecido:
```powershell
.\executar_sql.ps1 sql_scripts/04_views_grafana.sql
```

### Grafana não conecta ao PostgreSQL
- Verifique se o PostgreSQL está rodando: `docker compose ps postgres`
- Verifique se o datasource está configurado: http://localhost:3000/connections/datasources
- O datasource "PostgreSQL INMET" deve estar configurado automaticamente

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 Notas Importantes

- ⚠️ **Dados não são versionados**: Arquivos CSV e dados processados não são commitados (veja `.gitignore`)
- 📁 **Adicione seus CSVs**: Coloque arquivos CSV do INMET em `fastapi/app/data/raw/`
- 🎨 **Dashboard automático**: O Grafana já vem com dashboard provisionado
- 🔄 **Primeira execução**: Pode demorar mais tempo para baixar imagens Docker

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

**Disciplina:** Análise e Visualização de Dados - 2025.2  
**Instituição:** CESAR School  
**Projeto:** Classificação de Intensidade de Precipitação (Problema 7.8)

---

## 🙏 Agradecimentos

- INMET (Instituto Nacional de Meteorologia) pelos dados meteorológicos
- Comunidade open-source pelas ferramentas utilizadas

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Verifique a seção [Troubleshooting](#-troubleshooting)
2. Consulte a documentação adicional
3. Abra uma issue no repositório

---

**Desenvolvido com ❤️ para análise de dados meteorológicos**

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela! ⭐**

</div>
