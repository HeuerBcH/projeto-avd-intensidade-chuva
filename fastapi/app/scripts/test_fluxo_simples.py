#!/usr/bin/env python3
"""
Script simples para testar o fluxo ThingsBoard -> FastAPI -> S3 -> PostgreSQL
"""
import requests
import sys
import json

BASE_URL = "http://localhost:8000"

def test_step(name, endpoint, method="GET", data=None):
    """Testa um passo do fluxo"""
    print(f"\n[{name}]")
    print("-" * 60)
    
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=20)
        else:
            response = requests.post(url, json=data, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] {result.get('message', 'Sucesso')}")
            return True, result
        else:
            print(f"[ERRO] Status {response.status_code}: {response.text[:200]}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"[ERRO] Timeout - requisição demorou mais de 20s")
        return False, None
    except Exception as e:
        print(f"[ERRO] {str(e)[:200]}")
        return False, None

def main():
    print("=" * 60)
    print("TESTE DO FLUXO: ThingsBoard -> FastAPI -> S3 -> PostgreSQL")
    print("=" * 60)
    
    # Passo 1: Verificar conexões
    print("\n>>> PASSO 1: Verificando conexões")
    ok1, _ = test_step("ThingsBoard", "/test-thingsboard")
    ok2, _ = test_step("S3/MinIO", "/test-connection")
    ok3, _ = test_step("PostgreSQL", "/test-db")
    
    if not (ok1 and ok2 and ok3):
        print("\n[ERRO] Algumas conexões falharam. Verifique os serviços.")
        return False
    
    # Passo 2: Verificar dispositivos
    print("\n>>> PASSO 2: Verificando dispositivos no ThingsBoard")
    ok, result = test_step("Listar dispositivos", "/devices")
    
    if not ok:
        print("\n[ERRO] Não foi possível listar dispositivos")
        return False
    
    total = result.get('total', 0)
    devices = result.get('devices', [])
    weather_stations = [d for d in devices if 'Estacao_' in d.get('name', '')]
    
    print(f"   Total de dispositivos: {total}")
    print(f"   Estações meteorológicas: {len(weather_stations)}")
    
    if total == 0:
        print("\n[AVISO] Nenhum dispositivo encontrado.")
        print("   Execute: curl -X POST http://localhost:8000/populate-thingsboard")
        return False
    
    # Passo 3: Testar ingestão (com timeout curto para não travar)
    print("\n>>> PASSO 3: Testando ingestão (pode demorar...)")
    print("   Aguarde... isso pode levar alguns minutos se houver muitos dados.")
    
    try:
        # Usa timeout maior para a ingestão
        response = requests.post(
            f"{BASE_URL}/ingest-from-thingsboard",
            timeout=300  # 5 minutos
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'unknown')
            
            if status == 'success':
                print(f"[OK] Ingestão concluída!")
                print(f"   - Registros processados: {result.get('total_records', 0):,}")
                print(f"   - Estações: {result.get('estacoes_processadas', 0)}")
                print(f"   - Inseridos no PostgreSQL: {result.get('registros_inseridos', 0):,}")
                print(f"   - Arquivo S3: {result.get('file_saved', 'N/A')}")
            elif status == 'warning':
                print(f"[AVISO] {result.get('message', 'Aviso')}")
                return False
            else:
                print(f"[ERRO] Status: {status}")
                print(f"   Mensagem: {result.get('message', 'Sem mensagem')}")
                return False
        else:
            print(f"[ERRO] Status HTTP {response.status_code}")
            print(f"   Resposta: {response.text[:300]}")
            return False
            
    except requests.exceptions.Timeout:
        print("[AVISO] Ingestão demorou mais de 5 minutos.")
        print("   Isso pode ser normal se houver muitos dados históricos.")
        print("   Verifique os logs: docker logs fastapi-ingestao")
        return False
    except Exception as e:
        print(f"[ERRO] {str(e)}")
        return False
    
    # Passo 4: Verificar dados no banco
    print("\n>>> PASSO 4: Verificando dados no PostgreSQL")
    ok, result = test_step("Estatísticas", "/stats")
    
    if ok:
        stats = result.get('stats', {})
        print(f"   - Estações: {stats.get('total_estacoes', 0)}")
        print(f"   - Registros: {stats.get('total_registros', 0):,}")
        print(f"   - Período: {stats.get('periodo_inicio', 'N/A')} até {stats.get('periodo_fim', 'N/A')}")
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print("[OK] Fluxo testado com sucesso!")
    print("   ThingsBoard -> FastAPI -> S3 -> PostgreSQL")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


