# fastapi/app/services/main.py
from fastapi import FastAPI, HTTPException
from pathlib import Path
from .data_loader import load_local_data
from .s3_service import upload_to_minio

app = FastAPI(title="INMET Data Pipeline - Dados Locais 2024/2025")

@app.get("/")
def home():
    return {"message": "API de ingestão de dados INMET (modo local)"}

@app.post("/ingest")
def ingest_data():
    """
    Lê arquivos locais da pasta /data/raw e envia para o bucket MinIO/S3.
    """
    try:
        files = load_local_data()
        uploaded = []

        for file_path in files:
            upload_to_minio(file_path)
            uploaded.append(file_path.name)

        return {"status": "success", "arquivos_enviados": uploaded}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
