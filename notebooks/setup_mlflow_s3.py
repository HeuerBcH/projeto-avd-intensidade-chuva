#!/usr/bin/env python3
"""
Script para configurar o bucket MLFlow no MinIO
Execute este script antes de usar o MLFlow com S3
"""
import boto3
from botocore.client import Config
import sys

# Configurações do MinIO
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "mlflow-artifacts"

def create_bucket_if_not_exists():
    """Cria o bucket mlflow-artifacts no MinIO se não existir"""
    try:
        # Cria cliente S3 para MinIO
        s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        # Lista buckets existentes
        buckets = s3_client.list_buckets()
        bucket_names = [b['Name'] for b in buckets.get('Buckets', [])]
        
        if BUCKET_NAME in bucket_names:
            print(f"✅ Bucket '{BUCKET_NAME}' já existe no MinIO")
            return True
        
        # Cria o bucket
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket '{BUCKET_NAME}' criado com sucesso no MinIO")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar bucket: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Configuração do MLFlow S3 (MinIO)")
    print("=" * 60)
    
    success = create_bucket_if_not_exists()
    
    if success:
        print("\n✅ Configuração concluída!")
        print(f"   Bucket: {BUCKET_NAME}")
        print(f"   Endpoint: {MINIO_ENDPOINT}")
        print("\n📝 Próximos passos:")
        print("   1. Reinicie o container MLFlow: docker restart mlflow")
        print("   2. Configure as variáveis de ambiente no notebook:")
        print("      os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'")
        print("      os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'")
        print("      os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://minio:9000'")
        print("      os.environ['AWS_S3_FORCE_PATH_STYLE'] = 'true'")
    else:
        print("\n❌ Falha na configuração")
        sys.exit(1)

