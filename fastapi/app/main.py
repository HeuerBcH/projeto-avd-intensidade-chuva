from fastapi import FastAPI, HTTPException
from services.inmet_service import get_inmet_data
from services.s3_service import upload_to_s3

app = FastAPI(title="INMET Data Ingestion API")

@app.get("/")
def home():
    return {"message": "API de Ingestão de dados do INMET - Ativa"}

@app.post("/ingest")
def ingest_data():
    try:
        # 1. Coleta os dados do INMET
        df = get_inmet_data()

        # 2. Envia para o MinIO/S3
        file_path = upload_to_s3(df)

        return {"status": "success", "file_uploaded": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))