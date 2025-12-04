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
    print(f"Aguardando {service_name} ficar disponivel...")
    for i in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"OK: {service_name} esta disponivel!")
                return True
        except:
            pass
        time.sleep(RETRY_DELAY)
        print(f"   Tentativa {i+1}/{MAX_RETRIES}...")
    print(f"ERRO: {service_name} nao ficou disponivel apos {MAX_RETRIES * RETRY_DELAY} segundos")
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
                        print(f"OK: ThingsBoard ja esta populado com {len(devices)} dispositivos e {total_points} pontos de telemetria")
                        return True
        return False
    except:
        return False

def populate_thingsboard():
    """Popula ThingsBoard com dados dos CSVs"""
    print("\nPopulando ThingsBoard com dados historicos...")
    print("   (Isso pode levar varios minutos dependendo da quantidade de dados)")
    try:
        response = requests.post(f"{FASTAPI_URL}/populate-thingsboard", timeout=1800)  # 30 minutos
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                total_records = data.get("total_records", 0)
                print(f"OK: ThingsBoard populado com sucesso! ({total_records} registros)")
                # Mostra ultimas linhas do output se disponivel
                if "output" in data and data["output"]:
                    print("\nUltimas linhas do processo:")
                    for line in data["output"][-5:]:
                        if line.strip():
                            print(f"   {line}")
                return True
            else:
                error_msg = data.get("message", "Erro desconhecido")
                print(f"AVISO: {error_msg}")
                # Mostra erros se disponivel
                if "error" in data and data["error"]:
                    print("\nErros encontrados:")
                    for line in data["error"]:
                        if line.strip():
                            print(f"   {line}")
                return False
        else:
            print(f"ERRO ao popular ThingsBoard: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalhes: {error_data.get('detail', 'Sem detalhes')}")
            except:
                print(f"   Resposta: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print("AVISO: Timeout ao popular ThingsBoard")
        print("   O processo pode estar demorando muito. Verifique manualmente:")
        print("   POST http://localhost:8000/populate-thingsboard")
        return False
    except Exception as e:
        print(f"ERRO ao popular ThingsBoard: {e}")
        import traceback
        traceback.print_exc()
        return False

def ingest_from_thingsboard():
    """Ingere dados do ThingsBoard para S3 e PostgreSQL"""
    print("\nIngerindo dados do ThingsBoard para S3 e PostgreSQL...")
    try:
        response = requests.post(f"{FASTAPI_URL}/ingest-from-thingsboard", timeout=600)  # 10 minutos
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                records = data.get("registros_inseridos", 0)
                print(f"OK: Ingestao concluida! {records} registros inseridos no PostgreSQL")
                return True
            else:
                print(f"AVISO: {data.get('message', 'Erro desconhecido')}")
                return False
        else:
            print(f"ERRO na ingestao: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"ERRO ao ingerir dados: {e}")
        return False

def main():
    """Executa o pipeline completo"""
    print("=" * 60)
    print("INICIALIZACAO AUTOMATICA DO PIPELINE INMET")
    print("=" * 60)
    
    # 1. Aguarda FastAPI
    if not wait_for_service(f"{FASTAPI_URL}/", "FastAPI"):
        print("ERRO: FastAPI nao esta disponivel")
        return 1
    
    # 2. Aguarda ThingsBoard (tenta conectar via API interna primeiro)
    print("\nVerificando ThingsBoard...")
    thingsboard_ready = False
    for i in range(MAX_RETRIES):
        try:
            # Tenta conectar via hostname do Docker
            response = requests.get("http://thingsboard:9090/api/auth/login", timeout=5)
            thingsboard_ready = True
            print("OK: ThingsBoard esta disponivel!")
            break
        except:
            try:
                # Tenta conectar via localhost
                response = requests.get("http://localhost:9090/api/auth/login", timeout=5)
                thingsboard_ready = True
                print("OK: ThingsBoard esta disponivel!")
                break
            except:
                pass
        time.sleep(RETRY_DELAY)
        print(f"   Tentativa {i+1}/{MAX_RETRIES}...")
    
    if not thingsboard_ready:
        print("ERRO: ThingsBoard nao esta disponivel")
        print("   Verifique se o container thingsboard esta rodando: docker ps | grep thingsboard")
        return 1
    
    # 3. Verifica se há arquivos CSV antes de tentar popular
    print("\nVerificando arquivos CSV...")
    from pathlib import Path
    csv_dirs = [
        Path("/app/data/raw"),  # Dentro do container
        Path("fastapi/app/data/raw"),  # Caminho relativo
        Path("../fastapi/app/data/raw")  # Alternativo
    ]
    
    csv_files = []
    csv_dir = None
    for dir_path in csv_dirs:
        if dir_path.exists():
            csv_files = list(dir_path.glob("*.csv")) + list(dir_path.glob("*.CSV"))
            if csv_files:
                csv_dir = dir_path
                break
    
    if not csv_files:
        print("AVISO: Nenhum arquivo CSV encontrado!")
        print("   Coloque arquivos CSV em: fastapi/app/data/raw/")
        print("   O ThingsBoard nao sera populado automaticamente.")
    else:
        print(f"OK: Encontrados {len(csv_files)} arquivos CSV em {csv_dir}")
        
        # 4. Verifica se ThingsBoard já está populado
        if not check_thingsboard_populated():
            # 5. Popula ThingsBoard
            if not populate_thingsboard():
                print("AVISO: ThingsBoard pode nao ter sido populado completamente")
                print("   Execute manualmente: POST http://localhost:8000/populate-thingsboard")
        else:
            print("ThingsBoard ja esta populado, pulando populacao...")
    
    # 6. Ingestão do ThingsBoard para S3 e PostgreSQL (só se ThingsBoard estiver populado)
    if csv_files:
        if not ingest_from_thingsboard():
            print("AVISO: Ingestao pode nao ter sido concluida")
            print("   Execute manualmente: POST http://localhost:8000/ingest-from-thingsboard")
    else:
        print("\nAVISO: Ingestao nao sera executada (nao ha arquivos CSV)")
    
    print("\n" + "=" * 60)
    print("OK: PIPELINE INICIALIZADO!")
    print("=" * 60)
    print("\nProximos passos:")
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

