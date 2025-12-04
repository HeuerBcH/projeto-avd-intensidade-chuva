#!/usr/bin/env python3
"""
Script de inicialização automática do pipeline
Executa o fluxo completo: ThingsBoard → S3 → PostgreSQL
"""
import sys
import time
import requests
from pathlib import Path

# Adiciona o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

FASTAPI_URL = "http://localhost:8000"
MAX_RETRIES = 30
RETRY_DELAY = 5

def wait_for_service(url: str, service_name: str):
    """Aguarda serviço ficar disponível"""
    print(f"⏳ Aguardando {service_name} ficar disponível...")
    for i in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} está disponível!")
                return True
        except:
            pass
        time.sleep(RETRY_DELAY)
        print(f"   Tentativa {i+1}/{MAX_RETRIES}...")
    print(f"❌ {service_name} não ficou disponível após {MAX_RETRIES * RETRY_DELAY} segundos")
    return False

def check_thingsboard_populated():
    """Verifica se ThingsBoard já tem dados"""
    try:
        response = requests.get(f"{FASTAPI_URL}/devices", timeout=10)
        if response.status_code == 200:
            data = response.json()
            devices = data.get("devices", [])
            if len(devices) > 0:
                # Verifica se tem telemetria
                telemetry_response = requests.get(f"{FASTAPI_URL}/devices/telemetry", timeout=30)
                if telemetry_response.status_code == 200:
                    telemetry_data = telemetry_response.json()
                    total_points = telemetry_data.get("total_telemetry_points", 0)
                    if total_points > 0:
                        print(f"✅ ThingsBoard já está populado com {len(devices)} dispositivos e {total_points} pontos de telemetria")
                        return True
        return False
    except:
        return False

def populate_thingsboard():
    """Popula ThingsBoard com dados dos CSVs"""
    print("\n📤 Populando ThingsBoard com dados históricos...")
    try:
        response = requests.post(f"{FASTAPI_URL}/populate-thingsboard", timeout=1800)  # 30 minutos
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print(f"✅ ThingsBoard populado com sucesso!")
                return True
            else:
                print(f"⚠️  Aviso: {data.get('message', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Erro ao popular ThingsBoard: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("⚠️  Timeout ao popular ThingsBoard (pode estar processando, verifique manualmente)")
        return False
    except Exception as e:
        print(f"❌ Erro ao popular ThingsBoard: {e}")
        return False

def ingest_from_thingsboard():
    """Ingere dados do ThingsBoard para S3 e PostgreSQL"""
    print("\n📥 Ingerindo dados do ThingsBoard para S3 e PostgreSQL...")
    try:
        response = requests.post(f"{FASTAPI_URL}/ingest-from-thingsboard", timeout=600)  # 10 minutos
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                records = data.get("registros_inseridos", 0)
                print(f"✅ Ingestão concluída! {records} registros inseridos no PostgreSQL")
                return True
            else:
                print(f"⚠️  Aviso: {data.get('message', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Erro na ingestão: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao ingerir dados: {e}")
        return False

def main():
    """Executa o pipeline completo"""
    print("=" * 60)
    print("🚀 INICIALIZAÇÃO AUTOMÁTICA DO PIPELINE INMET")
    print("=" * 60)
    
    # 1. Aguarda FastAPI
    if not wait_for_service(f"{FASTAPI_URL}/", "FastAPI"):
        print("❌ Falha: FastAPI não está disponível")
        return 1
    
    # 2. Aguarda ThingsBoard
    if not wait_for_service("http://localhost:9090/api/auth/login", "ThingsBoard"):
        print("❌ Falha: ThingsBoard não está disponível")
        return 1
    
    # 3. Verifica se ThingsBoard já está populado
    if not check_thingsboard_populated():
        # 4. Popula ThingsBoard
        if not populate_thingsboard():
            print("⚠️  Aviso: ThingsBoard pode não ter sido populado completamente")
            print("   Execute manualmente: POST http://localhost:8000/populate-thingsboard")
    
    # 5. Ingestão do ThingsBoard para S3 e PostgreSQL
    if not ingest_from_thingsboard():
        print("⚠️  Aviso: Ingestão pode não ter sido concluída")
        print("   Execute manualmente: POST http://localhost:8000/ingest-from-thingsboard")
    
    print("\n" + "=" * 60)
    print("✅ PIPELINE INICIALIZADO COM SUCESSO!")
    print("=" * 60)
    print("\n📊 Próximos passos:")
    print("   1. Acesse JupyterLab: http://localhost:1010 (token: avd2025)")
    print("   2. Execute os notebooks em ordem:")
    print("      - 01_eda_exploracao.ipynb")
    print("      - 02_tratamento_limpeza.ipynb")
    print("      - 03_modelagem_mlflow.ipynb")
    print("   3. Acesse MLFlow: http://localhost:5000")
    print("   4. Configure Grafana: http://localhost:3000")
    print("\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

