# fastapi/app/services/s3_service.py
import boto3
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do .env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Cria o cliente S3 (compatível com MinIO ou AWS)
s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def upload_to_minio(file_path: Path):
    """
    Envia o arquivo local para o bucket configurado no .env.
    """
    bucket = os.getenv("S3_BUCKET_NAME", "inmet-data")
    key = f"raw/{file_path.name}"

    try:
        s3.upload_file(str(file_path), bucket, key)
        print(f"✅ Enviado: {file_path.name} → s3://{bucket}/{key}")
    except Exception as e:
        raise RuntimeError(f"Erro ao enviar {file_path.name}: {e}")
