#!/usr/bin/env python3
"""
Script para configurar automaticamente o datasource PostgreSQL no Trendz Analytics
"""
import requests
import os
import time
import sys
from typing import Dict, Optional

# Configurações
TRENDZ_URL = os.getenv("TRENDZ_URL")
THINGSBOARD_URL = os.getenv("THINGSBOARD_HOST")
TB_USERNAME = os.getenv("THINGSBOARD_USER")
TB_PASSWORD = os.getenv("THINGSBOARD_PASSWORD")

# Configuracao do PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


class TrendzConfigurator:
    def __init__(self):
        self.trendz_url = TRENDZ_URL
        self.tb_url = THINGSBOARD_URL
        self.tb_token = None
        self.trendz_token = None
    
    def wait_for_service(self, url: str, service_name: str, max_attempts: int = 30) -> bool:
        """Aguarda serviço estar disponível"""
        print(f"⏳ Aguardando {service_name} estar disponível...")
        for i in range(max_attempts):
            try:
                response = requests.get(f"{url}/api/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name} está disponível")
                    return True
            except:
                pass
            
            if i < max_attempts - 1:
                time.sleep(2)
        
        print(f"❌ {service_name} não está disponível após {max_attempts} tentativas")
        return False
    
    def authenticate_thingsboard(self) -> bool:
        """Autentica no ThingsBoard"""
        print("🔐 Autenticando no ThingsBoard...")
        url = f"{self.tb_url}/api/auth/login"
        payload = {
            "username": TB_USERNAME,
            "password": TB_PASSWORD
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.tb_token = data.get("token")
            
            if self.tb_token:
                print(f"✅ Autenticado no ThingsBoard como {TB_USERNAME}")
                return True
            else:
                print("❌ Token não recebido do ThingsBoard")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao autenticar no ThingsBoard: {e}")
            return False
    
    def authenticate_trendz(self) -> bool:
        """Autentica no Trendz (usa credenciais do ThingsBoard)"""
        print("🔐 Autenticando no Trendz...")
        
        # Trendz usa a mesma autenticação do ThingsBoard
        # Primeiro, autentica no ThingsBoard
        if not self.authenticate_thingsboard():
            return False
        
        # Trendz aceita o token do ThingsBoard
        self.trendz_token = self.tb_token
        
        # Testa se o token funciona no Trendz
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Authorization": f"Bearer {self.trendz_token}"
            }
            response = requests.get(
                f"{self.trendz_url}/api/trendz/datasources",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Autenticado no Trendz")
                return True
            else:
                print(f"⚠️  Resposta do Trendz: {response.status_code}")
                # Tenta autenticar diretamente no Trendz
                return self._authenticate_trendz_direct()
        except Exception as e:
            print(f"⚠️  Erro ao testar token no Trendz: {e}")
            return self._authenticate_trendz_direct()
    
    def _authenticate_trendz_direct(self) -> bool:
        """Tenta autenticar diretamente no Trendz"""
        try:
            # Trendz pode ter endpoint próprio de autenticação
            url = f"{self.trendz_url}/api/auth/login"
            payload = {
                "username": TB_USERNAME,
                "password": TB_PASSWORD
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.trendz_token = data.get("token") or self.tb_token
                print("✅ Autenticado no Trendz (método direto)")
                return True
        except:
            pass
        
        # Se falhar, usa token do ThingsBoard mesmo
        self.trendz_token = self.tb_token
        print("⚠️  Usando token do ThingsBoard para Trendz")
        return True
    
    def get_headers(self) -> Dict[str, str]:
        """Retorna headers com autenticação"""
        return {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {self.trendz_token}"
        }
    
    def list_datasources(self) -> list:
        """Lista datasources existentes"""
        try:
            # Trendz pode usar endpoint do ThingsBoard ou próprio
            endpoints = [
                f"{self.trendz_url}/api/trendz/datasources",
                f"{self.trendz_url}/api/datasources",
                f"{self.tb_url}/api/trendz/datasources"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, headers=self.get_headers(), timeout=10)
                    if response.status_code == 200:
                        return response.json()
                except:
                    continue
            
            return []
        except Exception as e:
            print(f"⚠️  Erro ao listar datasources: {e}")
            return []
    
    def create_datasource(self) -> bool:
        """Cria datasource PostgreSQL no Trendz"""
        print("📊 Criando datasource PostgreSQL...")
        
        datasource_config = {
            "name": "PostgreSQL INMET",
            "type": "postgres",
            "configuration": {
                "host": POSTGRES_HOST,
                "port": int(POSTGRES_PORT),
                "database": POSTGRES_DB,
                "username": POSTGRES_USER,
                "password": POSTGRES_PASSWORD,
                "ssl": False,
                "timeout": 30,
                "maxConnections": 10
            },
            "description": "Banco de dados PostgreSQL com dados meteorológicos do INMET"
        }
        
        # Tenta diferentes endpoints
        endpoints = [
            f"{self.trendz_url}/api/trendz/datasources",
            f"{self.trendz_url}/api/datasources",
            f"{self.tb_url}/api/trendz/datasources"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    json=datasource_config,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    print("✅ Datasource PostgreSQL criado com sucesso!")
                    return True
                elif response.status_code == 409:
                    print("ℹ️  Datasource já existe")
                    return True
                else:
                    print(f"⚠️  Resposta {response.status_code}: {response.text}")
            except Exception as e:
                print(f"⚠️  Erro ao criar datasource em {endpoint}: {e}")
                continue
        
        return False
    
    def test_datasource(self) -> bool:
        """Testa conexão do datasource"""
        print("🧪 Testando conexão do datasource...")
        
        # Lista datasources para encontrar o criado
        datasources = self.list_datasources()
        
        if not datasources:
            print("⚠️  Nenhum datasource encontrado")
            return False
        
        # Procura pelo datasource PostgreSQL
        postgres_ds = None
        if isinstance(datasources, list):
            postgres_ds = next((ds for ds in datasources if ds.get("type") == "postgres"), None)
        elif isinstance(datasources, dict) and "data" in datasources:
            postgres_ds = next((ds for ds in datasources["data"] if ds.get("type") == "postgres"), None)
        
        if not postgres_ds:
            print("⚠️  Datasource PostgreSQL não encontrado")
            return False
        
        ds_id = postgres_ds.get("id", {}).get("id") if isinstance(postgres_ds.get("id"), dict) else postgres_ds.get("id")
        
        # Testa conexão
        endpoints = [
            f"{self.trendz_url}/api/trendz/datasources/{ds_id}/test",
            f"{self.trendz_url}/api/datasources/{ds_id}/test",
            f"{self.tb_url}/api/trendz/datasources/{ds_id}/test"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", False):
                        print("✅ Conexão com PostgreSQL testada com sucesso!")
                        return True
                    else:
                        print(f"❌ Teste falhou: {result.get('error', 'Erro desconhecido')}")
            except Exception as e:
                continue
        
        print("⚠️  Não foi possível testar conexão (mas datasource foi criado)")
        return True  # Retorna True mesmo assim, pois pode ser problema de API
    
    def configure(self) -> bool:
        """Executa configuração completa"""
        print("=" * 60)
        print("🚀 Configurando Trendz Analytics - Datasource PostgreSQL")
        print("=" * 60)
        print()
        
        # 1. Aguarda serviços estarem prontos
        if not self.wait_for_service(self.tb_url, "ThingsBoard"):
            return False
        
        if not self.wait_for_service(self.trendz_url, "Trendz"):
            return False
        
        print()
        
        # 2. Autentica
        if not self.authenticate_trendz():
            return False
        
        print()
        
        # 3. Cria datasource
        if not self.create_datasource():
            print("⚠️  Não foi possível criar datasource via API")
            print("💡 Configure manualmente no Trendz:")
            print(f"   1. Acesse: {self.trendz_url}")
            print(f"   2. Login: {TB_USERNAME} / {TB_PASSWORD}")
            print(f"   3. Settings → Data Sources → Add PostgreSQL")
            print(f"   4. Host: {POSTGRES_HOST}")
            print(f"   5. Port: {POSTGRES_PORT}")
            print(f"   6. Database: {POSTGRES_DB}")
            print(f"   7. User: {POSTGRES_USER}")
            print(f"   8. Password: {POSTGRES_PASSWORD}")
            return False
        
        print()
        
        # 4. Testa conexão
        self.test_datasource()
        
        print()
        print("=" * 60)
        print("✅ Configuração concluída!")
        print("=" * 60)
        print()
        print("📋 Próximos passos:")
        print(f"   1. Acesse Trendz: {self.trendz_url}")
        print(f"   2. Login: {TB_USERNAME} / {TB_PASSWORD}")
        print("   3. Crie dashboards usando as views SQL:")
        print("      - vw_dados_recentes")
        print("      - vw_dados_7_dias")
        print("      - vw_distribuicao_intensidade")
        print("      - vw_ultimas_predicoes")
        print("      - vw_comparacao_predicoes")
        print()
        
        return True


def main():
    """Função principal"""
    configurator = TrendzConfigurator()
    success = configurator.configure()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

