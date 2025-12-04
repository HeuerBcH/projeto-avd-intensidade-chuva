# fastapi/app/services/s3_service.py
import boto3
import os
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# As variaveis de ambiente sao carregadas automaticamente pelo docker-compose.yml
# via env_file: .env (nao precisa load_dotenv dentro do container)

# Cria o cliente S3 (compatível com MinIO ou AWS)
s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def ensure_bucket_exists(bucket_name: str = None):
    """
    Garante que o bucket existe, criando-o se necessário.
    """
    if bucket_name is None:
        bucket_name = os.getenv("S3_BUCKET_NAME")
    
    try:
        # Tenta verificar se o bucket existe
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' já existe")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404':
            # Bucket não existe, vamos criar
            try:
                s3.create_bucket(Bucket=bucket_name)
                print(f"✅ Bucket '{bucket_name}' criado com sucesso")
            except Exception as create_error:
                raise RuntimeError(f"Erro ao criar bucket '{bucket_name}': {create_error}")
        else:
            raise RuntimeError(f"Erro ao verificar bucket '{bucket_name}': {e}")

def test_connection():
    """
    Testa a conexão com o MinIO/S3.
    Retorna True se a conexão for bem-sucedida, False caso contrário.
    """
    try:
        # Lista buckets para testar conexão
        s3.list_buckets()
        print("✅ Conexão com MinIO/S3 estabelecida com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com MinIO/S3: {e}")
        return False

def upload_to_minio(file_path: Path):
    """
    Envia o arquivo local para o bucket configurado no .env.
    Garante que o bucket existe antes de fazer upload.
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    key = f"raw/{file_path.name}"

    # Garante que o bucket existe
    ensure_bucket_exists(bucket)

    try:
        s3.upload_file(str(file_path), bucket, key)
        print(f"✅ Enviado: {file_path.name} → s3://{bucket}/{key}")
    except Exception as e:
        raise RuntimeError(f"Erro ao enviar {file_path.name}: {e}")
