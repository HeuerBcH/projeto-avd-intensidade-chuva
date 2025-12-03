#!/usr/bin/env python3
"""
Script de validação do pipeline completo:
ThingsBoard → FastAPI → S3 → PostgreSQL
"""
import requests
import sys
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_step(step_num, text):
    print(f"\n[{step_num}] {text}")
    print("-" * 80)

def test_endpoint(endpoint, method="GET", data=None):
    """Testa um endpoint e retorna a resposta"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=45)  # Aumentado para 45s
        elif method == "POST":
            response = requests.post(url, json=data, timeout=600)  # 10 minutos para ingest (pode processar muitos dados)
        else:
            return None, f"Método {method} não suportado"
        
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.Timeout:
        return None, "Timeout - requisição demorou muito"
    except requests.exceptions.RequestException as e:
        return None, f"Erro na requisição: {e}"

def main():
    print_header("VALIDAÇÃO DO PIPELINE COMPLETO")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    # Passo 1: Testar conexões
    print_step(1, "Testando conexões com serviços")
    
    # Test ThingsBoard
    result, error = test_endpoint("/test-thingsboard")
    if error:
        print(f"[ERRO] ThingsBoard: {error}")
        return False
    print(f"[OK] ThingsBoard: {result.get('message', 'OK')}")
    
    # Test S3
    result, error = test_endpoint("/test-connection")
    if error:
        print(f"[ERRO] S3/MinIO: {error}")
        return False
    print(f"[OK] S3/MinIO: {result.get('message', 'OK')}")
    
    # Test PostgreSQL
    result, error = test_endpoint("/test-db")
    if error:
        print(f"[ERRO] PostgreSQL: {error}")
        return False
    print(f"[OK] PostgreSQL: {result.get('message', 'OK')}")
    
    # Passo 2: Verificar dispositivos no ThingsBoard
    print_step(2, "Verificando dispositivos no ThingsBoard")
    result, error = test_endpoint("/devices")
    if error:
        print(f"❌ Erro ao listar dispositivos: {error}")
        return False
    
    total_devices = result.get('total', 0)
    devices = result.get('devices', [])
    
    if total_devices == 0:
        print("[AVISO] Nenhum dispositivo encontrado no ThingsBoard")
        print("   Execute: curl -X POST http://localhost:8000/populate-thingsboard")
        return False
    
    print(f"[OK] Encontrados {total_devices} dispositivos")
    
    # Filtra apenas estações meteorológicas
    weather_stations = [d for d in devices if 'Estacao_' in d.get('name', '')]
    print(f"   - {len(weather_stations)} estacoes meteorologicas")
    print(f"   - {total_devices - len(weather_stations)} outros dispositivos")
    
    if len(weather_stations) == 0:
        print("[AVISO] Nenhuma estacao meteorologica encontrada")
        print("   Execute: curl -X POST http://localhost:8000/populate-thingsboard")
        return False
    
    # Passo 3: Executar ingestão
    print_step(3, "Executando ingestão do ThingsBoard")
    print("   Isso pode demorar alguns minutos...")
    
    start_time = time.time()
    result, error = test_endpoint("/ingest-from-thingsboard", method="POST")
    elapsed_time = time.time() - start_time
    
    if error:
        print(f"❌ Erro na ingestão: {error}")
        return False
    
    status = result.get('status', 'unknown')
    if status == 'warning':
        print(f"[AVISO] {result.get('message', 'Aviso')}")
        return False
    elif status != 'success':
        print(f"[ERRO] Status: {status}")
        print(f"   Mensagem: {result.get('message', 'Sem mensagem')}")
        return False
    
    print(f"[OK] Ingestao concluida em {elapsed_time:.2f} segundos")
    print(f"   - Total de registros processados: {result.get('total_records', 0):,}")
    print(f"   - Estações processadas: {result.get('estacoes_processadas', 0)}")
    print(f"   - Registros inseridos no PostgreSQL: {result.get('registros_inseridos', 0):,}")
    print(f"   - Arquivo salvo no S3: {result.get('file_saved', 'N/A')}")
    
    # Passo 4: Verificar dados no PostgreSQL
    print_step(4, "Verificando dados no PostgreSQL")
    result, error = test_endpoint("/stats")
    if error:
        print(f"[AVISO] Nao foi possivel verificar estatisticas: {error}")
    else:
        stats = result.get('stats', {})
        print(f"[OK] Estatisticas do banco:")
        print(f"   - Total de estacoes: {stats.get('total_estacoes', 0)}")
        print(f"   - Total de registros: {stats.get('total_registros', 0):,}")
        print(f"   - Periodo: {stats.get('periodo_inicio', 'N/A')} ate {stats.get('periodo_fim', 'N/A')}")
    
    # Resumo final
    print_header("RESUMO DA VALIDACAO")
    
    if status == 'success' and result.get('registros_inseridos', 0) > 0:
        print("[OK] PIPELINE VALIDADO COM SUCESSO!")
        print("\nFluxo completo funcionando:")
        print("  ThingsBoard -> FastAPI -> S3 -> PostgreSQL")
        return True
    else:
        print("[AVISO] Pipeline executado, mas sem dados inseridos")
        print("   Verifique se ha telemetria no ThingsBoard")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

