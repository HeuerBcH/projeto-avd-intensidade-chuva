# fastapi/app/services/main.py
from fastapi import FastAPI, HTTPException
from pathlib import Path
from .data_loader import load_local_data
from .s3_service import upload_to_minio, test_connection, ensure_bucket_exists
from .db_service import test_db_connection, get_table_count, insert_estacao, insert_dados_meteorologicos_batch
from .csv_processor import parse_inmet_csv

app = FastAPI(title="INMET Data Pipeline - Dados Locais 2024/2025")

@app.get("/")
def home():
    return {
        "message": "API de ingestão de dados INMET (modo local)",
        "endpoints": {
            "test_s3": "/test-connection",
            "test_db": "/test-db",
            "ingest": "/ingest",
            "load_to_db": "/load-to-db",
            "stats": "/stats"
        }
    }

@app.get("/test-connection")
def test_s3_connection():
    """
    Testa a conexão com o MinIO/S3.
    """
    try:
        connection_ok = test_connection()
        if connection_ok:
            ensure_bucket_exists()
            return {
                "status": "success",
                "message": "Conexão com MinIO/S3 estabelecida com sucesso",
                "bucket_ready": True
            }
        else:
            return {
                "status": "error",
                "message": "Falha ao conectar com MinIO/S3"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
def ingest_data():
    """
    Lê arquivos locais da pasta /data/raw e envia para o bucket MinIO/S3.
    """
    try:
        # Testa conexão antes de processar
        if not test_connection():
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com MinIO/S3. Verifique se o serviço está rodando."
            )
        
        # Garante que o bucket existe
        ensure_bucket_exists()
        
        files = load_local_data()
        uploaded = []

        for file_path in files:
            upload_to_minio(file_path)
            uploaded.append(file_path.name)

        return {
            "status": "success",
            "arquivos_enviados": uploaded,
            "total": len(uploaded)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-db")
def test_db():
    """
    Testa a conexão com o PostgreSQL.
    """
    try:
        connection_ok = test_db_connection()
        if connection_ok:
            estacoes_count = get_table_count("estacoes")
            dados_count = get_table_count("dados_meteorologicos")
            return {
                "status": "success",
                "message": "Conexão com PostgreSQL estabelecida com sucesso",
                "estacoes": estacoes_count,
                "dados_meteorologicos": dados_count
            }
        else:
            return {
                "status": "error",
                "message": "Falha ao conectar com PostgreSQL"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-to-db")
def load_to_database():
    """
    Processa arquivos CSV locais e carrega no PostgreSQL.
    """
    try:
        # Testa conexões
        if not test_db_connection():
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com PostgreSQL. Verifique se o serviço está rodando."
            )
        
        files = load_local_data()
        total_estacoes = 0
        total_registros = 0
        processed_files = []
        
        for file_path in files:
            try:
                print(f"\n📄 Processando: {file_path.name}")
                
                # Processa o CSV
                resultado = parse_inmet_csv(file_path)
                estacao_info = resultado['estacao']
                dados = resultado['dados']
                
                # Insere estação
                insert_estacao(
                    codigo_wmo=estacao_info['codigo_wmo'],
                    regiao=estacao_info.get('regiao', ''),
                    uf=estacao_info.get('uf', ''),
                    nome=estacao_info.get('nome', ''),
                    latitude=estacao_info.get('latitude'),
                    longitude=estacao_info.get('longitude'),
                    altitude=estacao_info.get('altitude'),
                    data_fundacao=estacao_info.get('data_fundacao')
                )
                total_estacoes += 1
                
                # Insere dados em lotes
                if dados:
                    batch_size = 1000
                    for i in range(0, len(dados), batch_size):
                        batch = dados[i:i + batch_size]
                        inserted = insert_dados_meteorologicos_batch(batch)
                        total_registros += inserted
                
                processed_files.append({
                    "arquivo": file_path.name,
                    "estacao": estacao_info.get('nome', ''),
                    "registros": len(dados)
                })
                
            except Exception as e:
                print(f"❌ Erro ao processar {file_path.name}: {e}")
                processed_files.append({
                    "arquivo": file_path.name,
                    "erro": str(e)
                })
                continue
        
        return {
            "status": "success",
            "total_arquivos": len(files),
            "estacoes_processadas": total_estacoes,
            "total_registros": total_registros,
            "arquivos": processed_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    """
    Retorna estatísticas do banco de dados.
    """
    try:
        estacoes_count = get_table_count("estacoes")
        dados_count = get_table_count("dados_meteorologicos")
        
        return {
            "estacoes": estacoes_count,
            "dados_meteorologicos": dados_count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
