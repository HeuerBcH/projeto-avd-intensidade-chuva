"""
Serviço para integração com ThingsBoard
Consome dados da API do ThingsBoard e processa
"""
import requests
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

THINGSBOARD_HOST = os.getenv("THINGSBOARD_HOST", "http://thingsboard:9090")
THINGSBOARD_USER = os.getenv("THINGSBOARD_USER", "tenant@thingsboard.org")
THINGSBOARD_PASSWORD = os.getenv("THINGSBOARD_PASSWORD", "tenant")


class ThingsBoardService:
    def __init__(self):
        self.host = THINGSBOARD_HOST
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica no ThingsBoard"""
        url = f"{self.host}/api/auth/login"
        payload = {
            "username": THINGSBOARD_USER,
            "password": THINGSBOARD_PASSWORD
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            self.token = response.json()["token"]
            print("Autenticado no ThingsBoard")
            return True
        except Exception as e:
            print(f"Erro ao autenticar no ThingsBoard: {e}")
            return False
    
    def _get_headers(self):
        """Retorna headers com autenticação"""
        return {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {self.token}"
        }
    
    def get_all_devices(self) -> List[Dict]:
        """Lista todos os dispositivos"""
        url = f"{self.host}/api/tenant/devices?pageSize=100&page=0"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            devices = response.json().get("data", [])
            return devices
        except Exception as e:
            print(f"Erro ao listar dispositivos: {e}")
            return []
    
    def get_device_telemetry(self, device_id: str, keys: List[str], 
                            start_ts: Optional[int] = None, 
                            end_ts: Optional[int] = None) -> Dict:
        """
        Busca telemetria de um dispositivo
        
        Args:
            device_id: ID do dispositivo
            keys: Lista de chaves de telemetria (ex: ['temperatura_ar_c', 'precipitacao_mm'])
            start_ts: Timestamp inicial em milissegundos
            end_ts: Timestamp final em milissegundos
        """
        # Se não especificado, busca últimas 24 horas
        if not end_ts:
            end_ts = int(datetime.now().timestamp() * 1000)
        if not start_ts:
            start_ts = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
        
        keys_str = ",".join(keys)
        url = f"{self.host}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
        params = {
            "keys": keys_str,
            "startTs": start_ts,
            "endTs": end_ts,
            "limit": 10000
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), 
                                   params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao buscar telemetria: {e}")
            return {}
    
    def get_device_attributes(self, device_id: str) -> Dict:
        """Busca atributos de um dispositivo"""
        url = f"{self.host}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao buscar atributos: {e}")
            return {}


def test_connection() -> bool:
    """Testa conexão com ThingsBoard"""
    try:
        service = ThingsBoardService()
        return service.token is not None
    except:
        return False


def get_all_weather_data() -> List[Dict]:
    """
    Busca dados de todas as estações meteorológicas
    Retorna lista de dicionários com dados processados
    """
    service = ThingsBoardService()
    
    if not service.token:
        return []
    
    devices = service.get_all_devices()
    all_data = []
    
    telemetry_keys = [
        "precipitacao_mm",
        "temperatura_ar_c",
        "umidade_rel_pct",
        "pressao_mb",
        "vento_velocidade_ms",
        "vento_direcao_graus",
        "radiacao_kjm2"
    ]
    
    for device in devices:
        device_id = device['id']['id']
        device_name = device['name']
        
        # Busca atributos
        attributes = service.get_device_attributes(device_id)
        
        # Busca telemetria
        telemetry = service.get_device_telemetry(device_id, telemetry_keys)
        
        # Processa dados
        for key, values in telemetry.items():
            for item in values:
                data_point = {
                    "device_id": device_id,
                    "device_name": device_name,
                    "timestamp": item['ts'],
                    "key": key,
                    "value": item['value']
                }
                # Adiciona atributos
                data_point.update(attributes)
                all_data.append(data_point)
    
    return all_data
