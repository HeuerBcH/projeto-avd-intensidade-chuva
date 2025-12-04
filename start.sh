#!/bin/bash

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Pipeline INMET - Iniciando Serviços                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verifica se o Docker está rodando
echo "🔍 Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERRO: Docker não está rodando."
    echo "   Por favor, inicie o Docker e tente novamente."
    exit 1
fi
echo "✅ Docker está rodando!"
echo ""

# Cria diretórios necessários
echo "📁 Criando estrutura de diretórios..."
mkdir -p data/postgres data/minio data/raw mlflow/artifacts thingsboard/data thingsboard/logs grafana/data
touch data/.gitkeep data/raw/.gitkeep mlflow/.gitkeep thingsboard/.gitkeep 2>/dev/null
echo "✅ Estrutura de diretórios pronta!"
echo ""

# Verifica se o arquivo .env existe
ENV_FILE="fastapi/app/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚙️  Criando arquivo .env..."
    cat > "$ENV_FILE" << EOF
# Configurações do MinIO/S3
S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=inmet-data

# Configurações do PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=inmet_db
POSTGRES_USER=inmet_user
POSTGRES_PASSWORD=inmet_password

# Configurações do ThingsBoard
THINGSBOARD_HOST=http://thingsboard:9090
THINGSBOARD_USER=tenant@thingsboard.org
THINGSBOARD_PASSWORD=tenant
EOF
    echo "✅ Arquivo .env criado!"
else
    echo "✅ Arquivo .env já existe"
fi

echo ""

# Verifica se há arquivos CSV
CSV_PATH="fastapi/app/data/raw"
if [ -d "$CSV_PATH" ]; then
    CSV_COUNT=$(find "$CSV_PATH" -maxdepth 1 -type f \( -name "*.csv" -o -name "*.CSV" \) 2>/dev/null | wc -l)
    if [ "$CSV_COUNT" -eq 0 ]; then
        echo "⚠️  AVISO: Nenhum arquivo CSV encontrado em $CSV_PATH"
        echo "   Você precisará adicionar arquivos CSV do INMET para processar dados."
    else
        echo "✅ Encontrados $CSV_COUNT arquivo(s) CSV"
    fi
fi

echo ""

# Para containers existentes
echo "🛑 Parando containers existentes (se houver)..."
docker compose down > /dev/null 2>&1
sleep 2

echo ""
echo "🚀 Iniciando containers Docker..."
docker compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Erro ao iniciar containers Docker!"
    exit 1
fi

echo ""
echo "⏳ Aguardando serviços iniciarem..."
sleep 20

echo ""
echo "✅ Serviços iniciados!"
echo ""

# Verifica se FastAPI está disponível
echo "🔍 Verificando se FastAPI está pronto..."
FASTAPI_READY=false
for i in {1..40}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        FASTAPI_READY=true
        echo "✅ FastAPI está pronto!"
        break
    else
        if [ $i -lt 40 ]; then
            echo "   Aguardando FastAPI... ($i/40)"
            sleep 3
        fi
    fi
done

if [ "$FASTAPI_READY" = false ]; then
    echo "⚠️  FastAPI não está respondendo ainda. Aguarde alguns minutos."
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Pipeline iniciado com sucesso!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🌐 Acesse os seguintes serviços:"
echo ""
echo "   📊 FastAPI:        http://localhost:8000/docs"
echo "   📈 Grafana:       http://localhost:3000 (admin/admin)"
echo "   🔬 JupyterLab:    http://localhost:1010 (token: avd2025)"
echo "   🤖 MLFlow:        http://localhost:5000"
echo "   📦 MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "   🌍 ThingsBoard:   http://localhost:9090 (tenant@thingsboard.org/tenant)"
echo ""

echo "📋 Próximos passos:"
echo ""
echo "   1️⃣  Se você tem arquivos CSV do INMET:"
echo "      - Coloque-os em: fastapi/app/data/raw/"
echo "      - Execute: POST http://localhost:8000/populate-thingsboard"
echo "      - Execute: POST http://localhost:8000/ingest-from-thingsboard"
echo ""
echo "   2️⃣  Ou carregue diretamente no banco:"
echo "      - Execute: POST http://localhost:8000/load-to-db"
echo ""
echo "   3️⃣  Classifique a intensidade de chuva:"
echo "      - Acesse JupyterLab e execute: notebooks/02_tratamento_limpeza.ipynb"
echo ""
echo "   4️⃣  Treine modelos ML:"
echo "      - Execute: notebooks/03_modelagem_mlflow.ipynb"
echo ""
echo "   5️⃣  Visualize no Grafana:"
echo "      - Acesse http://localhost:3000"
echo "      - Dashboard 'Intensidade de Chuva' já está disponível!"
echo ""

echo "📚 Comandos úteis:"
echo "   - Ver logs:        docker compose logs -f"
echo "   - Parar serviços:  ./stop.sh"
echo "   - Reiniciar:       docker compose restart"
echo ""
