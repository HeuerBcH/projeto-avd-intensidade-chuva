# fastapi/app/services/main.py
from fastapi import FastAPI, HTTPException
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
from .data_loader import load_local_data
from .s3_service import upload_to_minio, test_connection, ensure_bucket_exists
from .db_service import test_db_connection, get_table_count, insert_estacao, insert_dados_meteorologicos_batch
from .csv_processor import parse_inmet_csv
from .thingsboard_service import (
    test_connection as test_tb_connection,
    get_all_weather_data,
    ThingsBoardService
)
from .mlflow_service import (
    list_models,
    load_best_model,
    predict,
    predict_batch,
    get_model_info
)

app = FastAPI(title="INMET Data Pipeline - Dados Locais 2024/2025")

@app.get("/")
def home():
    return {
        "message": "API de ingestão de dados INMET - Pipeline IoT",
        "endpoints": {
            "test_s3": "/test-connection",
            "test_db": "/test-db",
            "test_thingsboard": "/test-thingsboard",
            "populate_thingsboard": "/populate-thingsboard",
            "ingest": "/ingest (consome ThingsBoard)",
            "load_to_db": "/load-to-db",
            "devices": "/devices",
            "devices_telemetry": "/devices/telemetry",
            "ingest_from_thingsboard": "/ingest-from-thingsboard",
            "stats": "/stats",
            "models": "/models",
            "models_load": "/models/load",
            "models_info": "/models/info",
            "predict": "/predict",
            "predict_batch": "/predict/batch"
        }
    }

@app.get("/test-connection")
def test_s3_connection():
    """
    Testa a conexão com o MinIO/S3.
    """
    try:
        connection_ok = test_connection()
        if connection_ok:
            ensure_bucket_exists()
            return {
                "status": "success",
                "message": "Conexão com MinIO/S3 estabelecida com sucesso",
                "bucket_ready": True
            }
        else:
            return {
                "status": "error",
                "message": "Falha ao conectar com MinIO/S3"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
def ingest_data():
    """
    Endpoint principal de ingestão - consome dados do ThingsBoard e salva no S3.
    Este é o fluxo correto: ThingsBoard → FastAPI → S3
    """
    # Redireciona para o endpoint que consome ThingsBoard
    return ingest_from_thingsboard()

@app.get("/test-db")
def test_db():
    """
    Testa a conexão com o PostgreSQL.
    """
    try:
        connection_ok = test_db_connection()
        if connection_ok:
            estacoes_count = get_table_count("estacoes")
            dados_count = get_table_count("dados_meteorologicos")
            return {
                "status": "success",
                "message": "Conexão com PostgreSQL estabelecida com sucesso",
                "estacoes": estacoes_count,
                "dados_meteorologicos": dados_count
            }
        else:
            return {
                "status": "error",
                "message": "Falha ao conectar com PostgreSQL"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-to-db")
def load_to_database():
    """
    Processa arquivos CSV locais e carrega no PostgreSQL.
    """
    try:
        # Testa conexões
        if not test_db_connection():
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com PostgreSQL. Verifique se o serviço está rodando."
            )
        
        files = load_local_data()
        total_estacoes = 0
        total_registros = 0
        processed_files = []
        
        for file_path in files:
            try:
                print(f"\n📄 Processando: {file_path.name}")
                
                # Processa o CSV
                resultado = parse_inmet_csv(file_path)
                estacao_info = resultado['estacao']
                dados = resultado['dados']
                
                # Insere estação
                insert_estacao(
                    codigo_wmo=estacao_info['codigo_wmo'],
                    regiao=estacao_info.get('regiao', ''),
                    uf=estacao_info.get('uf', ''),
                    nome=estacao_info.get('nome', ''),
                    latitude=estacao_info.get('latitude'),
                    longitude=estacao_info.get('longitude'),
                    altitude=estacao_info.get('altitude'),
                    data_fundacao=estacao_info.get('data_fundacao')
                )
                total_estacoes += 1
                
                # Insere dados em lotes
                if dados:
                    batch_size = 1000
                    for i in range(0, len(dados), batch_size):
                        batch = dados[i:i + batch_size]
                        inserted = insert_dados_meteorologicos_batch(batch)
                        total_registros += inserted
                
                processed_files.append({
                    "arquivo": file_path.name,
                    "estacao": estacao_info.get('nome', ''),
                    "registros": len(dados)
                })
                
            except Exception as e:
                print(f"❌ Erro ao processar {file_path.name}: {e}")
                processed_files.append({
                    "arquivo": file_path.name,
                    "erro": str(e)
                })
                continue
        
        return {
            "status": "success",
            "total_arquivos": len(files),
            "estacoes_processadas": total_estacoes,
            "total_registros": total_registros,
            "arquivos": processed_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    """
    Retorna estatísticas do banco de dados.
    """
    try:
        estacoes_count = get_table_count("estacoes")
        dados_count = get_table_count("dados_meteorologicos")
        
        return {
            "estacoes": estacoes_count,
            "dados_meteorologicos": dados_count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-thingsboard")
def test_thingsboard():
    """
    Testa a conexão com o ThingsBoard.
    """
    try:
        connection_ok = test_tb_connection()
        if connection_ok:
            return {
                "status": "success",
                "message": "Conexão com ThingsBoard estabelecida com sucesso"
            }
        else:
            return {
                "status": "error",
                "message": "Falha ao conectar com ThingsBoard"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
def list_devices():
    """
    Lista todos os dispositivos IoT cadastrados no ThingsBoard.
    """
    try:
        service = ThingsBoardService()
        devices = service.get_all_devices()
        
        return {
            "status": "success",
            "total": len(devices),
            "devices": [
                {
                    "id": d['id']['id'],
                    "name": d['name'],
                    "type": d['type'],
                    "label": d.get('label', '')
                }
                for d in devices
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/devices/fix-names")
def fix_device_names():
    """
    Corrige nomes de dispositivos que contêm espaços, substituindo por underscores.
    Isso resolve problemas de exibição na interface do ThingsBoard.
    """
    try:
        service = ThingsBoardService()
        devices = service.get_all_devices()
        
        if not devices:
            return {
                "status": "warning",
                "message": "Nenhum dispositivo encontrado",
                "fixed": [],
                "checked": 0
            }
        
        fixed_devices = []
        checked_devices = []
        
        for device in devices:
            device_id = device['id']['id']
            current_name = device.get('name', '')
            current_label = device.get('label', current_name)
            
            checked_devices.append({
                "device_id": device_id,
                "name": current_name,
                "has_spaces": ' ' in current_name
            })
            
            # Verifica se há espaços no nome
            if ' ' in current_name:
                # Substitui espaços por underscores
                new_name = current_name.replace(' ', '_')
                new_label = current_label.replace(' ', '_') if current_label else new_name
                
                print(f"🔄 Tentando corrigir: {current_name} → {new_name}")
                
                # Atualiza dispositivo
                if service.update_device_name(device_id, new_name, new_label):
                    fixed_devices.append({
                        "device_id": device_id,
                        "old_name": current_name,
                        "new_name": new_name
                    })
                    print(f"✅ Corrigido: {current_name} → {new_name}")
                else:
                    print(f"❌ Falha ao corrigir: {current_name}")
        
        return {
            "status": "success",
            "message": f"{len(fixed_devices)} dispositivos corrigidos de {len(devices)} verificados",
            "fixed": fixed_devices,
            "checked": checked_devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices/telemetry")
def check_telemetry():
    """
    Verifica a quantidade de telemetria em cada dispositivo do ThingsBoard.
    Retorna estatísticas de dados por dispositivo.
    """
    try:
        service = ThingsBoardService()
        devices = service.get_all_devices()
        
        if not devices:
            return {
                "status": "warning",
                "message": "Nenhum dispositivo encontrado no ThingsBoard",
                "devices": []
            }
        
        telemetry_keys = [
            "precipitacao_mm",
            "temperatura_ar_c",
            "umidade_rel_pct",
            "pressao_mb",
            "vento_velocidade_ms",
            "vento_direcao_graus",
            "radiacao_kjm2"
        ]
        
        devices_info = []
        total_telemetry_points = 0
        
        for device in devices:
            device_id = device['id']['id']
            device_name = device['name']
            
            # Busca telemetria
            telemetry = service.get_device_telemetry(device_id, telemetry_keys)
            
            # Conta pontos de telemetria
            device_telemetry_count = {}
            device_total_points = 0
            
            for key, values in telemetry.items():
                if isinstance(values, list):
                    count = len(values)
                    device_telemetry_count[key] = count
                    device_total_points += count
            
            total_telemetry_points += device_total_points
            
            # Busca atributos
            attributes = service.get_device_attributes(device_id)
            
            devices_info.append({
                "device_id": device_id,
                "device_name": device_name,
                "type": device.get('type', ''),
                "telemetry_keys": device_telemetry_count,
                "total_telemetry_points": device_total_points,
                "has_attributes": bool(attributes),
                "attributes_count": len(attributes) if isinstance(attributes, dict) else 0
            })
        
        return {
            "status": "success",
            "total_devices": len(devices),
            "total_telemetry_points": total_telemetry_points,
            "devices": devices_info,
            "summary": {
                "devices_with_telemetry": sum(1 for d in devices_info if d['total_telemetry_points'] > 0),
                "devices_without_telemetry": sum(1 for d in devices_info if d['total_telemetry_points'] == 0),
                "average_points_per_device": round(total_telemetry_points / len(devices), 2) if devices else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/populate-thingsboard")
def populate_thingsboard():
    """
    Popula o ThingsBoard com dados históricos dos CSVs.
    Cria dispositivos (estações) e envia telemetria.
    Execute este endpoint ANTES de usar /ingest.
    """
    try:
        import subprocess
        import sys
        from pathlib import Path
        
        # Verifica se ThingsBoard está acessível
        if not test_tb_connection():
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com ThingsBoard. Verifique se está rodando."
            )
        
        # Caminho do script de população (dentro do container)
        script_path = Path("/app/scripts/populate_thingsboard.py")
        
        # Se não encontrar, tenta caminho relativo (desenvolvimento local)
        if not script_path.exists():
            script_path = Path(__file__).parent.parent / "scripts" / "populate_thingsboard.py"
        
        if not script_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Script populate_thingsboard.py não encontrado. Procurado em: {script_path}"
            )
        
        print(f"📤 Executando script: {script_path}")
        
        # Executa o script
        # Timeout aumentado para 30 minutos (processar 24 CSVs pode demorar muito)
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(script_path.parent),
            timeout=1800  # 30 minutos de timeout
        )
        
        output_lines = result.stdout.split('\n') if result.stdout else []
        error_lines = result.stderr.split('\n') if result.stderr else []
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": "Erro ao executar script de população",
                "error": error_lines[-10:] if error_lines else "Sem mensagem de erro",
                "output": output_lines[-20:] if output_lines else []
            }
        
        # Extrai informações do output
        total_records = 0
        for line in output_lines:
            if "Total de registros enviados" in line or "Total enviado" in line:
                try:
                    # Tenta extrair número
                    import re
                    match = re.search(r'(\d{1,3}(?:[.,]\d{3})*)', line)
                    if match:
                        total_records = int(match.group(1).replace(',', '').replace('.', ''))
                except:
                    pass
        
        return {
            "status": "success",
            "message": "ThingsBoard populado com sucesso",
            "total_records": total_records,
            "output": output_lines[-30:] if output_lines else []  # Últimas 30 linhas
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Timeout ao executar script. O processo pode estar demorando muito."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-from-thingsboard")
def ingest_from_thingsboard():
    """
    Coleta dados do ThingsBoard e armazena no S3 e PostgreSQL.
    Este é o fluxo principal: ThingsBoard → FastAPI → S3 → PostgreSQL
    """
    try:
        # Testa conexões
        if not test_tb_connection():
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com ThingsBoard. Execute /populate-thingsboard primeiro."
            )
        
        if not test_connection():  # S3
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com MinIO/S3"
            )
        
        if not test_db_connection():  # PostgreSQL
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com PostgreSQL"
            )
        
        # Busca dados do ThingsBoard
        print("📡 Coletando dados do ThingsBoard...")
        service = ThingsBoardService()
        devices = service.get_all_devices()
        
        if not devices:
            return {
                "status": "warning",
                "message": "Nenhum dispositivo encontrado no ThingsBoard. Execute /populate-thingsboard primeiro."
            }
        
        # Telemetria keys esperadas
        telemetry_keys = [
            "precipitacao_mm",
            "temperatura_ar_c",
            "umidade_rel_pct",
            "pressao_mb",
            "vento_velocidade_ms",
            "vento_direcao_graus",
            "radiacao_kjm2"
        ]
        
        all_data = []
        total_records = 0
        
        # Processa cada dispositivo
        for device in devices:
            device_id = device['id']['id']
            device_name = device['name']
            
            # Busca atributos (informações da estação)
            attributes_raw = service.get_device_attributes(device_id)
            
            # Converte atributos para dicionário (pode vir como lista ou dict)
            attributes = {}
            if isinstance(attributes_raw, dict):
                attributes = attributes_raw
            elif isinstance(attributes_raw, list):
                # Se for lista, converte para dict
                for attr in attributes_raw:
                    if isinstance(attr, dict) and 'key' in attr and 'value' in attr:
                        attributes[attr['key']] = attr['value']
            
            # Busca telemetria (dados meteorológicos)
            telemetry = service.get_device_telemetry(device_id, telemetry_keys)
            
            # Processa telemetria e agrupa por timestamp
            records_by_ts = {}
            for key, values in telemetry.items():
                if not isinstance(values, list):
                    continue
                for item in values:
                    if not isinstance(item, dict) or 'ts' not in item:
                        continue
                    ts = item['ts']
                    if ts not in records_by_ts:
                        records_by_ts[ts] = {
                            "device_id": device_id,
                            "device_name": device_name,
                            "timestamp": ts,
                            **attributes  # Adiciona atributos da estação
                        }
                    records_by_ts[ts][key] = item.get('value')
            
            all_data.extend(records_by_ts.values())
            total_records += len(records_by_ts)
        
        if not all_data:
            return {
                "status": "warning",
                "message": "Nenhum dado de telemetria encontrado no ThingsBoard"
            }
        
        # Salva dados no S3 (formato JSON)
        import json
        import tempfile
        
        ensure_bucket_exists()
        s3_filename = f"thingsboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        temp_file = Path(tempfile.gettempdir()) / s3_filename
        
        # Salva arquivo temporário
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Upload para S3
        from .s3_service import upload_to_minio
        upload_to_minio(temp_file)
        s3_key = f"raw/{s3_filename}"
        
        # Remove arquivo temporário após upload
        try:
            temp_file.unlink()
        except:
            pass
        
        # Processa e insere no PostgreSQL
        estacoes_processadas = set()
        batch_data = []
        batch_size = 1000
        registros_inseridos = 0
        
        for record in all_data:
            try:
                # Extrai informações da estação
                codigo_wmo = record.get('codigo_wmo') or record.get('device_name', '').split('_')[1] if '_' in record.get('device_name', '') else None
                
                if not codigo_wmo:
                    continue
                
                # Insere estação (se ainda não foi inserida)
                if codigo_wmo not in estacoes_processadas:
                    insert_estacao(
                        codigo_wmo=codigo_wmo,
                        regiao=record.get('regiao', 'NORDESTE'),
                        uf=record.get('estado', 'PE'),
                        nome=record.get('nome', record.get('device_name', '')),
                        latitude=record.get('latitude'),
                        longitude=record.get('longitude'),
                        altitude=record.get('altitude')
                    )
                    estacoes_processadas.add(codigo_wmo)
                
                # Prepara dados meteorológicos
                from datetime import datetime as dt, time
                timestamp_utc = dt.fromtimestamp(record['timestamp'] / 1000)
                
                dados_meteorologicos = {
                    'codigo_wmo': codigo_wmo,
                    'data': timestamp_utc.date(),
                    'hora_utc': timestamp_utc.time(),
                    'timestamp_utc': timestamp_utc,  # Adiciona timestamp_utc explicitamente
                    'precipitacao_mm': record.get('precipitacao_mm'),
                    'temperatura_ar_c': record.get('temperatura_ar_c'),
                    'umidade_rel_horaria_pct': record.get('umidade_rel_pct'),
                    'pressao_estacao_mb': record.get('pressao_mb'),
                    'vento_velocidade_ms': record.get('vento_velocidade_ms'),
                    'vento_direcao_graus': record.get('vento_direcao_graus'),
                    'radiacao_global_kjm2': record.get('radiacao_kjm2')
                }
                
                # Adiciona à lista para inserção em lote
                batch_data.append(dados_meteorologicos)
                
                # Insere em lotes
                if len(batch_data) >= batch_size:
                    inserted = insert_dados_meteorologicos_batch(batch_data)
                    registros_inseridos += inserted
                    batch_data = []
                
            except Exception as e:
                print(f"Erro ao processar registro: {e}")
                continue
        
        # Insere lote final
        if batch_data:
            inserted = insert_dados_meteorologicos_batch(batch_data)
            registros_inseridos += inserted
        
        return {
            "status": "success",
            "message": "Dados coletados do ThingsBoard, salvos no S3 e inseridos no PostgreSQL",
            "total_records": total_records,
            "estacoes_processadas": len(estacoes_processadas),
            "registros_inseridos": registros_inseridos,
            "file_saved": s3_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINTS DE ML/PREDIÇÃO
# ============================================================================

class PredictionRequest(BaseModel):
    """Modelo de requisição para predição única"""
    precipitacao_mm: float
    pressao_estacao_mb: float
    pressao_max_mb: Optional[float] = 0.0
    pressao_min_mb: Optional[float] = 0.0
    temperatura_ar_c: float
    temperatura_max_c: Optional[float] = 0.0
    temperatura_min_c: Optional[float] = 0.0
    umidade_rel_horaria_pct: float
    umidade_rel_max_pct: Optional[float] = 0.0
    umidade_rel_min_pct: Optional[float] = 0.0
    vento_velocidade_ms: float
    vento_direcao_graus: Optional[float] = 0.0
    vento_rajada_max_ms: Optional[float] = 0.0
    radiacao_global_kjm2: Optional[float] = 0.0
    ano: Optional[int] = None
    mes: Optional[int] = None
    dia: Optional[int] = None
    hora: Optional[int] = None
    dia_semana: Optional[int] = None

@app.get("/models")
def list_available_models():
    """
    Lista todos os modelos disponíveis no MLFlow.
    """
    try:
        models = list_models()
        return {
            "status": "success",
            "total": len(models),
            "models": models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/load")
def load_model(model_name: Optional[str] = None):
    """
    Carrega um modelo específico do MLFlow.
    Se model_name não for fornecido, carrega o melhor modelo por accuracy.
    """
    try:
        success = load_best_model(model_name)
        if success:
            info = get_model_info()
            return {
                "status": "success",
                "message": f"Modelo carregado com sucesso",
                "model_info": info
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Modelo não encontrado{' para ' + model_name if model_name else ''}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/info")
def get_model_information():
    """
    Retorna informações sobre o modelo atualmente carregado.
    """
    try:
        info = get_model_info()
        return {
            "status": "success",
            "model_info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def make_prediction(request: PredictionRequest):
    """
    Faz uma predição de intensidade de chuva usando o modelo carregado.
    
    Recebe dados meteorológicos e retorna a predição de intensidade de chuva.
    """
    try:
        # Converte request para dict
        data = request.dict()
        
        # Preenche valores None com 0
        for key, value in data.items():
            if value is None:
                data[key] = 0.0
        
        # Extrai data/hora se disponível para calcular features temporais
        if data.get('ano') is None or data.get('mes') is None:
            from datetime import datetime
            now = datetime.now()
            if data.get('ano') is None:
                data['ano'] = now.year
            if data.get('mes') is None:
                data['mes'] = now.month
            if data.get('dia') is None:
                data['dia'] = now.day
            if data.get('hora') is None:
                data['hora'] = now.hour
            if data.get('dia_semana') is None:
                data['dia_semana'] = now.weekday()
        
        result = predict(data)
        return {
            "status": "success",
            "prediction": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
def make_batch_predictions(requests: List[PredictionRequest]):
    """
    Faz predições em lote para múltiplos registros.
    
    Útil para processar grandes volumes de dados de uma vez.
    """
    try:
        data_list = []
        for req in requests:
            data = req.dict()
            # Preenche valores None
            for key, value in data.items():
                if value is None:
                    data[key] = 0.0
            data_list.append(data)
        
        results = predict_batch(data_list)
        return {
            "status": "success",
            "total": len(results),
            "predictions": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
