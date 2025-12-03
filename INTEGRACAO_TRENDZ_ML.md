# 🔗 Integração Trendz com MLFlow via FastAPI

## ✅ Status: Endpoints Criados

Os endpoints de predição foram criados no FastAPI e estão prontos para uso no Trendz.

---

## 📋 Endpoints Disponíveis

### 1. **Listar Modelos** - `GET /models`

Lista todos os modelos disponíveis no MLFlow.

**Exemplo:**
```bash
curl http://localhost:8000/models
```

**Resposta:**
```json
{
  "status": "success",
  "total": 3,
  "models": [
    {
      "run_id": "a5c3be94398d45e78cd0cfe08f5cf092",
      "model_name": "RandomForest",
      "test_accuracy": 0.9998,
      "test_f1": 0.9998,
      "status": "FINISHED",
      "artifact_uri": "s3://mlflow-artifacts/..."
    }
  ]
}
```

---

### 2. **Carregar Modelo** - `POST /models/load`

Carrega um modelo específico do MLFlow. Se não especificar, carrega o melhor por accuracy.

**Exemplo:**
```bash
# Carregar melhor modelo automaticamente
curl -X POST http://localhost:8000/models/load

# Carregar modelo específico
curl -X POST "http://localhost:8000/models/load?model_name=RandomForest"
```

**Resposta:**
```json
{
  "status": "success",
  "message": "Modelo carregado com sucesso",
  "model_info": {
    "loaded": true,
    "model_name": "RandomForest",
    "model_type": "RandomForestClassifier",
    "has_scaler": true,
    "has_label_encoder": false
  }
}
```

---

### 3. **Informações do Modelo** - `GET /models/info`

Retorna informações sobre o modelo atualmente carregado.

**Exemplo:**
```bash
curl http://localhost:8000/models/info
```

---

### 4. **Predição Única** - `POST /predict`

Faz uma predição de intensidade de chuva.

**Exemplo:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "precipitacao_mm": 15.5,
    "pressao_estacao_mb": 1013.2,
    "temperatura_ar_c": 28.5,
    "umidade_rel_horaria_pct": 75.0,
    "vento_velocidade_ms": 3.2,
    "radiacao_global_kjm2": 2500.0
  }'
```

**Resposta:**
```json
{
  "status": "success",
  "prediction": {
    "prediction": "moderada",
    "prediction_code": 2,
    "probabilities": {
      "forte": 0.01,
      "leve": 0.15,
      "moderada": 0.70,
      "sem_chuva": 0.14
    },
    "model_name": "RandomForest"
  }
}
```

---

### 5. **Predições em Lote** - `POST /predict/batch`

Faz predições para múltiplos registros de uma vez.

**Exemplo:**
```bash
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {
      "precipitacao_mm": 15.5,
      "pressao_estacao_mb": 1013.2,
      "temperatura_ar_c": 28.5,
      "umidade_rel_horaria_pct": 75.0,
      "vento_velocidade_ms": 3.2
    },
    {
      "precipitacao_mm": 0.0,
      "pressao_estacao_mb": 1015.0,
      "temperatura_ar_c": 30.0,
      "umidade_rel_horaria_pct": 60.0,
      "vento_velocidade_ms": 2.5
    }
  ]'
```

---

## 🔧 Como Usar no Trendz

### Opção 1: Usar Widget HTTP Request (Recomendado)

1. **Acesse o Trendz**: http://localhost:8888
2. **Crie um Dashboard** ou edite um existente
3. **Adicione Widget**: Escolha "HTTP Request" ou "Custom Widget"
4. **Configure a URL**: `http://fastapi:8000/predict` (use nome do serviço Docker)
5. **Configure Método**: POST
6. **Configure Body**: Use dados do PostgreSQL ou ThingsBoard
7. **Exiba Resultado**: Mostre a predição no widget

### Opção 2: Usar Rule Chain no ThingsBoard

1. **Crie uma Rule Chain** no ThingsBoard
2. **Adicione Node HTTP Request**
3. **Configure**:
   - URL: `http://fastapi:8000/predict`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Body: Dados meteorológicos do dispositivo
4. **Salve predição** como atributo do dispositivo
5. **Exiba no Trendz** usando o atributo salvo

### Opção 3: Script Personalizado no Trendz

Se o Trendz suportar scripts customizados, você pode criar um script que:

```javascript
// Exemplo (pseudocódigo)
async function predictRainIntensity(data) {
  const response = await fetch('http://fastapi:8000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      precipitacao_mm: data.precipitacao_mm,
      pressao_estacao_mb: data.pressao_mb,
      temperatura_ar_c: data.temperatura_c,
      umidade_rel_horaria_pct: data.umidade_pct,
      vento_velocidade_ms: data.vento_ms
    })
  });
  const result = await response.json();
  return result.prediction.prediction;
}
```

---

## 📊 Estrutura de Dados

### Input (PredictionRequest)

```json
{
  "precipitacao_mm": 15.5,              // Obrigatório
  "pressao_estacao_mb": 1013.2,        // Obrigatório
  "pressao_max_mb": 1015.0,             // Opcional (default: 0.0)
  "pressao_min_mb": 1010.0,             // Opcional (default: 0.0)
  "temperatura_ar_c": 28.5,             // Obrigatório
  "temperatura_max_c": 30.0,            // Opcional (default: 0.0)
  "temperatura_min_c": 25.0,            // Opcional (default: 0.0)
  "umidade_rel_horaria_pct": 75.0,      // Obrigatório
  "umidade_rel_max_pct": 80.0,          // Opcional (default: 0.0)
  "umidade_rel_min_pct": 70.0,          // Opcional (default: 0.0)
  "vento_velocidade_ms": 3.2,           // Obrigatório
  "vento_direcao_graus": 180.0,         // Opcional (default: 0.0)
  "vento_rajada_max_ms": 5.0,           // Opcional (default: 0.0)
  "radiacao_global_kjm2": 2500.0,       // Opcional (default: 0.0)
  "ano": 2024,                           // Opcional (usa data atual se não fornecido)
  "mes": 12,                             // Opcional
  "dia": 3,                              // Opcional
  "hora": 14,                            // Opcional
  "dia_semana": 2                        // Opcional (0=segunda, 6=domingo)
}
```

### Output

```json
{
  "status": "success",
  "prediction": {
    "prediction": "moderada",            // Nome da classe predita
    "prediction_code": 2,                // Código numérico (0=forte, 1=leve, 2=moderada, 3=sem_chuva)
    "probabilities": {                   // Probabilidades (se disponível)
      "forte": 0.01,
      "leve": 0.15,
      "moderada": 0.70,
      "sem_chuva": 0.14
    },
    "model_name": "RandomForest"        // Nome do modelo usado
  }
}
```

---

## 🚀 Exemplo Completo de Uso

### 1. Carregar Modelo (opcional - carrega automaticamente no primeiro predict)

```bash
curl -X POST http://localhost:8000/models/load
```

### 2. Fazer Predição

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "precipitacao_mm": 25.0,
    "pressao_estacao_mb": 1010.5,
    "temperatura_ar_c": 26.0,
    "umidade_rel_horaria_pct": 85.0,
    "vento_velocidade_ms": 4.5,
    "vento_direcao_graus": 180.0,
    "radiacao_global_kjm2": 2000.0
  }'
```

### 3. Usar no Trendz

No Trendz, configure um widget que:
1. Busca dados do PostgreSQL ou ThingsBoard
2. Chama `/predict` para cada registro
3. Exibe a predição junto com os dados reais
4. Atualiza em tempo real

---

## ⚠️ Notas Importantes

1. **Primeira Predição**: Se nenhum modelo estiver carregado, o sistema tenta carregar automaticamente o melhor modelo.

2. **Normalização**: O modelo espera dados normalizados. O serviço aplica o scaler automaticamente se disponível.

3. **Features Temporais**: Se `ano`, `mes`, `dia`, `hora`, `dia_semana` não forem fornecidos, o sistema usa a data/hora atual.

4. **Valores Faltantes**: Valores `None` ou não fornecidos são preenchidos com `0.0`.

5. **URL no Docker**: Dentro do Docker, use `http://fastapi:8000` (nome do serviço). De fora, use `http://localhost:8000`.

---

## ✅ Checklist de Integração

- [x] Endpoints de predição criados
- [x] Serviço MLFlow implementado
- [x] Documentação criada
- [ ] Modelo treinado e salvo no MLFlow/S3
- [ ] Testar endpoints de predição
- [ ] Configurar Trendz para chamar FastAPI
- [ ] Criar visualizações no Trendz com predições

---

## 🔍 Troubleshooting

### Erro: "Nenhum modelo carregado"

**Solução**: Execute primeiro `/models/load` ou treine um modelo no notebook.

### Erro: "Modelo não encontrado"

**Solução**: Verifique se há modelos no MLFlow: `GET /models`

### Erro: "Connection refused"

**Solução**: Verifique se o FastAPI está rodando: `docker ps | grep fastapi`

### Predições incorretas

**Solução**: 
- Verifique se os dados estão na mesma escala do treinamento
- Verifique se todas as features estão sendo fornecidas
- Verifique se o modelo foi treinado corretamente

---

## 📝 Próximos Passos

1. **Treinar modelos** no notebook `03_modelagem_mlflow.ipynb`
2. **Testar endpoints** com dados reais
3. **Configurar Trendz** para usar os endpoints
4. **Criar visualizações** no Trendz mostrando predições

