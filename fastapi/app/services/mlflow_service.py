"""
Serviço para carregar modelos do MLFlow e fazer predições
"""
import os
import mlflow
import mlflow.sklearn
from typing import Dict, List, Optional
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Configurações
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
EXPERIMENT_NAME = "intensidade_chuva_classificacao"

# Configuração S3 (MinIO)
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin')
os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.getenv('MLFLOW_S3_ENDPOINT_URL', 'http://minio:9000')
os.environ['AWS_S3_FORCE_PATH_STYLE'] = os.getenv('AWS_S3_FORCE_PATH_STYLE', 'true')

# Cache do modelo carregado
_loaded_model = None
_loaded_model_name = None
_scaler = None
_label_encoder = None


def get_mlflow_client():
    """Retorna cliente MLFlow configurado"""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    return mlflow


def list_models() -> List[Dict]:
    """Lista todos os modelos disponíveis no MLFlow"""
    try:
        client = get_mlflow_client()
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        
        if not experiment:
            return []
        
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.test_accuracy DESC"],
            max_results=10
        )
        
        models = []
        for run in runs:
            model_name = run.data.tags.get('mlflow.runName', run.info.run_id)
            metrics = run.data.metrics
            
            models.append({
                "run_id": run.info.run_id,
                "model_name": model_name,
                "test_accuracy": metrics.get('test_accuracy', 0),
                "test_f1": metrics.get('test_f1', 0),
                "status": run.info.status,
                "artifact_uri": run.info.artifact_uri
            })
        
        return models
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")
        return []


def load_best_model(model_name: Optional[str] = None) -> bool:
    """
    Carrega o melhor modelo do MLFlow
    
    Args:
        model_name: Nome do modelo específico (opcional). Se None, carrega o melhor por accuracy.
    
    Returns:
        True se o modelo foi carregado com sucesso
    """
    global _loaded_model, _loaded_model_name, _scaler, _label_encoder
    
    try:
        client = get_mlflow_client()
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        
        if not experiment:
            print(f"Experimento '{EXPERIMENT_NAME}' não encontrado")
            return False
        
        # Busca runs
        if model_name:
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"tags.mlflow.runName = '{model_name}'",
                max_results=1
            )
        else:
            # Busca melhor modelo por accuracy
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["metrics.test_accuracy DESC"],
                max_results=1
            )
        
        if not runs:
            print(f"Nenhum modelo encontrado{' para ' + model_name if model_name else ''}")
            return False
        
        run = runs[0]
        run_id = run.info.run_id
        
        # Carrega modelo
        model_uri = f"runs:/{run_id}/model"
        _loaded_model = mlflow.sklearn.load_model(model_uri)
        _loaded_model_name = run.data.tags.get('mlflow.runName', run_id)
        
        # Tenta carregar scaler e label encoder se disponíveis
        try:
            scaler_uri = f"runs:/{run_id}/scaler"
            _scaler = mlflow.sklearn.load_model(scaler_uri)
        except:
            _scaler = None
            print("⚠️  Scaler não encontrado no run. Será necessário normalizar manualmente.")
        
        try:
            le_uri = f"runs:/{run_id}/label_encoder"
            _label_encoder = mlflow.sklearn.load_model(le_uri)
        except:
            _label_encoder = None
            print("⚠️  LabelEncoder não encontrado. Usando mapeamento padrão.")
        
        print(f"✅ Modelo carregado: {_loaded_model_name} (run_id: {run_id})")
        print(f"   Accuracy: {run.data.metrics.get('test_accuracy', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar modelo: {e}")
        import traceback
        traceback.print_exc()
        return False


def predict(data: Dict) -> Dict:
    """
    Faz predição usando o modelo carregado
    
    Args:
        data: Dicionário com features do modelo
        
    Returns:
        Dicionário com predição e probabilidades
    """
    global _loaded_model, _loaded_model_name
    
    if _loaded_model is None:
        # Tenta carregar automaticamente
        if not load_best_model():
            raise ValueError("Nenhum modelo carregado e não foi possível carregar automaticamente")
    
    # Mapeamento de classes (padrão se label_encoder não estiver disponível)
    class_mapping = {
        0: "forte",
        1: "leve",
        2: "moderada",
        3: "sem_chuva"
    }
    
    # Prepara features na ordem esperada
    feature_order = [
        'precipitacao_mm',
        'pressao_estacao_mb', 'pressao_max_mb', 'pressao_min_mb',
        'temperatura_ar_c', 'temperatura_max_c', 'temperatura_min_c',
        'umidade_rel_horaria_pct', 'umidade_rel_max_pct', 'umidade_rel_min_pct',
        'vento_velocidade_ms', 'vento_direcao_graus', 'vento_rajada_max_ms',
        'radiacao_global_kjm2',
        'ano', 'mes', 'dia', 'hora', 'dia_semana'
    ]
    
    # Extrai features na ordem correta
    features = []
    for feat in feature_order:
        value = data.get(feat, 0.0)
        if value is None:
            value = 0.0
        features.append(float(value))
    
    X = np.array([features])
    
    # Normaliza se scaler estiver disponível
    if _scaler is not None:
        X = _scaler.transform(X)
    
    # Faz predição
    prediction = _loaded_model.predict(X)[0]
    probabilities = None
    
    # Tenta obter probabilidades se o modelo suportar
    try:
        if hasattr(_loaded_model, 'predict_proba'):
            proba = _loaded_model.predict_proba(X)[0]
            probabilities = {
                class_mapping.get(i, f"class_{i}"): float(prob)
                for i, prob in enumerate(proba)
            }
    except:
        pass
    
    # Converte predição para nome da classe
    if _label_encoder is not None:
        try:
            class_name = _label_encoder.inverse_transform([prediction])[0]
        except:
            class_name = class_mapping.get(prediction, f"class_{prediction}")
    else:
        class_name = class_mapping.get(prediction, f"class_{prediction}")
    
    return {
        "prediction": class_name,
        "prediction_code": int(prediction),
        "probabilities": probabilities,
        "model_name": _loaded_model_name
    }


def predict_batch(data_list: List[Dict]) -> List[Dict]:
    """
    Faz predições em lote
    
    Args:
        data_list: Lista de dicionários com features
        
    Returns:
        Lista de predições
    """
    results = []
    for data in data_list:
        try:
            result = predict(data)
            results.append(result)
        except Exception as e:
            results.append({
                "error": str(e),
                "prediction": None
            })
    return results


def get_model_info() -> Dict:
    """Retorna informações sobre o modelo carregado"""
    global _loaded_model, _loaded_model_name
    
    if _loaded_model is None:
        return {
            "loaded": False,
            "message": "Nenhum modelo carregado"
        }
    
    return {
        "loaded": True,
        "model_name": _loaded_model_name,
        "model_type": type(_loaded_model).__name__,
        "has_scaler": _scaler is not None,
        "has_label_encoder": _label_encoder is not None
    }

