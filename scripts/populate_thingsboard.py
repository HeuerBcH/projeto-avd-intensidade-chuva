"""
Script para popular o ThingsBoard com dados históricos do INMET
Simula dispositivos IoT enviando telemetria
"""
import requests
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime
import sys

# Configurações do ThingsBoard
THINGSBOARD_HOST = "http://localhost:9090"
THINGSBOARD_USER = "tenant@thingsboard.org"
THINGSBOARD_PASSWORD = "tenant"

# Estações meteorológicas de Pernambuco (serão extraídas automaticamente dos CSVs)
ESTACOES = {}

class ThingsBoardClient:
    def __init__(self, host, username, password):
        self.host = host
        self.token = None
        self.login(username, password)
    
    def login(self, username, password):
        """Autentica no ThingsBoard e obtém token JWT"""
        url = f"{self.host}/api/auth/login"
        payload = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            self.token = response.json()["token"]
            print(f"Autenticado no ThingsBoard")
            return True
        except Exception as e:
            print(f"Erro ao autenticar: {e}")
            return False
    
    def get_headers(self):
        """Retorna headers com token de autenticação"""
        return {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {self.token}"
        }
    
    def create_device(self, device_name, device_type="weather_station"):
        """Cria um dispositivo no ThingsBoard"""
        url = f"{self.host}/api/device"
        payload = {
            "name": device_name,
            "type": device_type,
            "label": device_name
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.get_headers())
            response.raise_for_status()
            device = response.json()
            print(f"Dispositivo criado: {device_name} (ID: {device['id']['id']})")
            return device
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # Dispositivo já existe, buscar
                return self.get_device_by_name(device_name)
            else:
                print(f"Erro ao criar dispositivo {device_name}: {e}")
                return None
    
    def get_device_by_name(self, device_name):
        """Busca dispositivo pelo nome"""
        url = f"{self.host}/api/tenant/devices?deviceName={device_name}"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            device = response.json()
            print(f"ℹDispositivo já existe: {device_name}")
            return device
        except Exception as e:
            print(f"Erro ao buscar dispositivo: {e}")
            return None
    
    def get_device_token(self, device_id):
        """Obtém o token de acesso do dispositivo"""
        url = f"{self.host}/api/device/{device_id}/credentials"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            credentials = response.json()
            return credentials.get("credentialsId")
        except Exception as e:
            print(f"Erro ao obter token do dispositivo: {e}")
            return None
    
    def send_telemetry(self, device_token, telemetry_data):
        """Envia telemetria para um dispositivo"""
        url = f"{self.host}/api/v1/{device_token}/telemetry"
        
        try:
            response = requests.post(url, json=telemetry_data)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Erro ao enviar telemetria: {e}")
            return False
    
    def send_attributes(self, device_id, attributes):
        """Envia atributos para um dispositivo"""
        url = f"{self.host}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
        
        try:
            response = requests.post(url, json=attributes, headers=self.get_headers())
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Erro ao enviar atributos: {e}")
            return False


def process_csv_file(file_path, client, device_token, batch_size=100):
    """Processa arquivo CSV e envia dados para ThingsBoard"""
    print(f"\nProcessando: {file_path.name}")
    
    try:
        # Lê CSV (pula as 8 primeiras linhas de cabeçalho)
        df = pd.read_csv(file_path, sep=';', skiprows=8, encoding='latin-1', on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        
        # Filtra dados válidos
        df = df.dropna(subset=['Data', 'Hora UTC'])
        
        total_sent = 0
        batch = []
        
        for idx, row in df.iterrows():
            try:
                # Converte data e hora para timestamp
                data_str = str(row.get('Data', '')).strip()
                hora_str = str(row.get('Hora UTC', '')).strip().replace(' UTC', '').replace('UTC', '').strip()
                
                if not data_str or not hora_str or data_str == 'nan' or hora_str == 'nan':
                    continue
                
                # Cria timestamp
                timestamp = pd.to_datetime(f"{data_str} {hora_str[:2]}:{hora_str[2:]}", 
                                          format='%Y/%m/%d %H:%M')
                ts_ms = int(timestamp.timestamp() * 1000)
                
                # Função auxiliar para converter valores
                def parse_value(val):
                    if pd.isna(val) or val == '' or str(val).strip() == '':
                        return 0.0
                    try:
                        val_str = str(val).strip().replace(',', '.')
                        if val_str == '' or val_str.lower() in ['nan', 'none', 'null']:
                            return 0.0
                        return float(val_str)
                    except:
                        return 0.0
                
                # Prepara telemetria
                telemetry = {
                    "ts": ts_ms,
                    "values": {
                        "precipitacao_mm": parse_value(row.get('PRECIPITAÇÃO TOTAL, HORÁRIO (mm)')),
                        "temperatura_ar_c": parse_value(row.get('TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)')),
                        "umidade_rel_pct": parse_value(row.get('UMIDADE RELATIVA DO AR, HORARIA (%)')),
                        "pressao_mb": parse_value(row.get('PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)')),
                        "vento_velocidade_ms": parse_value(row.get('VENTO, VELOCIDADE HORARIA (m/s)')),
                        "vento_direcao_graus": parse_value(row.get('VENTO, DIREÇÃO HORARIA (gr) (° (gr))')),
                        "radiacao_kjm2": parse_value(row.get('RADIACAO GLOBAL (Kj/m²)'))
                    }
                }
                
                batch.append(telemetry)
                
                # Envia em lotes
                if len(batch) >= batch_size:
                    if client.send_telemetry(device_token, batch):
                        total_sent += len(batch)
                        print(f"Enviados {total_sent} registros...")
                    batch = []
                    time.sleep(0.1)  # Evita sobrecarga
                
            except Exception as e:
                continue
        
        # Envia lote final
        if batch:
            if client.send_telemetry(device_token, batch):
                total_sent += len(batch)
        
        print(f"Total enviado: {total_sent} registros")
        return total_sent
        
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        return 0


def extract_station_info(csv_file):
    """Extrai informações da estação do cabeçalho do CSV"""
    try:
        with open(csv_file, 'r', encoding='latin-1') as f:
            lines = [f.readline().strip() for _ in range(9)]
        
        # Extrai informações do cabeçalho (formato: CHAVE:;VALOR)
        info = {}
        
        for line in lines:
            if ':;' in line:
                key, value = line.split(':;', 1)
                key = key.strip()
                value = value.strip()
                
                if 'ESTACAO' in key:
                    info['nome'] = value
                elif 'CODIGO (WMO)' in key:
                    info['codigo'] = value
                    info['codigo_wmo'] = value
                elif 'LATITUDE' in key:
                    try:
                        info['latitude'] = float(value.replace(',', '.'))
                    except:
                        info['latitude'] = 0.0
                elif 'LONGITUDE' in key:
                    try:
                        info['longitude'] = float(value.replace(',', '.'))
                    except:
                        info['longitude'] = 0.0
                elif 'ALTITUDE' in key:
                    try:
                        info['altitude'] = float(value.replace(',', '.'))
                    except:
                        info['altitude'] = 0.0
        
        return info if 'codigo' in info else None
    except Exception as e:
        print(f"Erro ao extrair informacoes de {csv_file.name}: {e}")
        return None


def discover_stations(data_dir):
    """Descobre todas as estações a partir dos arquivos CSV"""
    stations = {}
    csv_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.CSV"))
    
    for csv_file in csv_files:
        info = extract_station_info(csv_file)
        if info and 'codigo' in info:
            codigo = info['codigo']
            # Evita duplicatas (mesma estação com arquivos de anos diferentes)
            if codigo not in stations:
                stations[codigo] = {
                    'nome': info.get('nome', 'DESCONHECIDO'),
                    'latitude': info.get('latitude', 0.0),
                    'longitude': info.get('longitude', 0.0),
                    'altitude': info.get('altitude', 0.0),
                    'codigo_wmo': info.get('codigo_wmo', '')
                }
    
    return stations


def main():
    print("="*80)
    print("IMPORTAÇÃO DE DADOS DO INMET PARA THINGSBOARD")
    print("="*80)
    
    # Descobre estações a partir dos CSVs
    data_dir = Path("fastapi/app/data/raw")
    
    if not data_dir.exists():
        print(f"Pasta não encontrada: {data_dir}")
        sys.exit(1)
    
    print(f"\nDescobrin estacoes em {data_dir}...")
    discovered_stations = discover_stations(data_dir)
    
    if not discovered_stations:
        print("ERRO: Nenhuma estacao encontrada nos arquivos CSV")
        sys.exit(1)
    
    print(f"Encontradas {len(discovered_stations)} estacoes:")
    for codigo, info in discovered_stations.items():
        print(f"   - {codigo}: {info['nome']}")
    
    # Conecta ao ThingsBoard
    print(f"\nConectando ao ThingsBoard...")
    client = ThingsBoardClient(THINGSBOARD_HOST, THINGSBOARD_USER, THINGSBOARD_PASSWORD)
    
    if not client.token:
        print("ERRO: Nao foi possivel conectar ao ThingsBoard")
        print("Certifique-se de que o ThingsBoard esta rodando em http://localhost:9090")
        sys.exit(1)
    
    # Cria dispositivos para cada estação
    print(f"\nCriando dispositivos no ThingsBoard...")
    devices = {}
    for codigo, info in discovered_stations.items():
        device_name = f"Estacao_{codigo}_{info['nome']}"
        device = client.create_device(device_name)
        
        if device:
            device_id = device['id']['id']
            device_token = client.get_device_token(device_id)
            
            # Envia atributos da estação
            attributes = {
                "codigo_wmo": info.get('codigo_wmo', codigo),
                "nome": info['nome'],
                "latitude": info['latitude'],
                "longitude": info['longitude'],
                "altitude": info.get('altitude', 0.0),
                "estado": "PE",
                "tipo": "Estação Automática INMET"
            }
            client.send_attributes(device_id, attributes)
            
            devices[codigo] = {
                "device": device,
                "token": device_token
            }
    
    print(f"{len(devices)} dispositivos configurados")
    
    # Processa arquivos CSV
    csv_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.CSV"))
    
    if not csv_files:
        print(f"ERRO: Nenhum arquivo CSV encontrado em {data_dir}")
        sys.exit(1)
    
    print(f"\nEncontrados {len(csv_files)} arquivos CSV")
    print(f"\nProcessando telemetria...")
    
    total_records = 0
    for csv_file in csv_files:
        # Identifica estação pelo nome do arquivo
        for codigo in discovered_stations.keys():
            if codigo in csv_file.name:
                if codigo in devices:
                    records = process_csv_file(
                        csv_file, 
                        client, 
                        devices[codigo]['token']
                    )
                    total_records += records
                break
    
    print("\n" + "="*80)
    print(f"IMPORTAÇÃO CONCLUÍDA!")
    print(f"Total de registros enviados: {total_records:,}")
    print(f"Acesse: {THINGSBOARD_HOST}")
    print("="*80)


if __name__ == "__main__":
    main()
