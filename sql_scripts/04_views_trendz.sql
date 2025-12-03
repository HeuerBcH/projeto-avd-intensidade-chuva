-- Views e tabelas específicas para Trendz Analytics

-- View para dados recentes (últimas 24h) com informações de estação
CREATE OR REPLACE VIEW vw_dados_recentes AS
SELECT 
    dm.id,
    dm.timestamp_utc,
    dm.codigo_wmo,
    e.nome as estacao_nome,
    e.uf,
    e.latitude,
    e.longitude,
    dm.precipitacao_mm,
    dm.intensidade_chuva,
    dm.temperatura_ar_c,
    dm.umidade_rel_horaria_pct,
    dm.pressao_estacao_mb,
    dm.vento_velocidade_ms,
    dm.radiacao_global_kjm2
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE dm.timestamp_utc >= NOW() - INTERVAL '24 hours'
ORDER BY dm.timestamp_utc DESC;

-- View para dados dos últimos 7 dias (otimizada para gráficos)
CREATE OR REPLACE VIEW vw_dados_7_dias AS
SELECT 
    DATE(dm.timestamp_utc) as data,
    dm.codigo_wmo,
    e.nome as estacao_nome,
    COUNT(*) as total_registros,
    AVG(dm.precipitacao_mm) as precip_media,
    SUM(dm.precipitacao_mm) as precip_total,
    MAX(dm.precipitacao_mm) as precip_max,
    AVG(dm.temperatura_ar_c) as temp_media,
    MAX(dm.temperatura_ar_c) as temp_max,
    MIN(dm.temperatura_ar_c) as temp_min,
    AVG(dm.umidade_rel_horaria_pct) as umidade_media,
    AVG(dm.pressao_estacao_mb) as pressao_media,
    AVG(dm.vento_velocidade_ms) as vento_medio,
    COUNT(CASE WHEN dm.intensidade_chuva = 'forte' THEN 1 END) as registros_forte,
    COUNT(CASE WHEN dm.intensidade_chuva = 'moderada' THEN 1 END) as registros_moderada,
    COUNT(CASE WHEN dm.intensidade_chuva = 'leve' THEN 1 END) as registros_leve,
    COUNT(CASE WHEN dm.intensidade_chuva = 'sem_chuva' THEN 1 END) as registros_sem_chuva
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE dm.timestamp_utc >= NOW() - INTERVAL '7 days'
GROUP BY DATE(dm.timestamp_utc), dm.codigo_wmo, e.nome
ORDER BY data DESC, e.nome;

-- View para distribuição de intensidade de chuva
CREATE OR REPLACE VIEW vw_distribuicao_intensidade AS
SELECT 
    intensidade_chuva,
    COUNT(*) as total_registros,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual,
    AVG(precipitacao_mm) as precip_media,
    MAX(precipitacao_mm) as precip_max,
    MIN(precipitacao_mm) as precip_min
FROM dados_meteorologicos
WHERE intensidade_chuva IS NOT NULL
GROUP BY intensidade_chuva
ORDER BY 
    CASE intensidade_chuva
        WHEN 'forte' THEN 1
        WHEN 'moderada' THEN 2
        WHEN 'leve' THEN 3
        WHEN 'sem_chuva' THEN 4
    END;

-- Tabela para armazenar predições do modelo ML
CREATE TABLE IF NOT EXISTS predicoes_intensidade (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    codigo_wmo VARCHAR(10),
    estacao_nome VARCHAR(255),
    -- Dados de entrada
    precipitacao_mm NUMERIC(10, 2),
    pressao_estacao_mb NUMERIC(10, 2),
    temperatura_ar_c NUMERIC(5, 2),
    umidade_rel_horaria_pct NUMERIC(5, 2),
    vento_velocidade_ms NUMERIC(5, 2),
    -- Resultado da predição
    intensidade_predita VARCHAR(20),
    probabilidade_forte NUMERIC(5, 4),
    probabilidade_moderada NUMERIC(5, 4),
    probabilidade_leve NUMERIC(5, 4),
    probabilidade_sem_chuva NUMERIC(5, 4),
    modelo_usado VARCHAR(100),
    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_predicoes_timestamp ON predicoes_intensidade(timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_predicoes_codigo_wmo ON predicoes_intensidade(codigo_wmo);
CREATE INDEX IF NOT EXISTS idx_dados_meteorologicos_timestamp ON dados_meteorologicos(timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_dados_meteorologicos_intensidade ON dados_meteorologicos(intensidade_chuva);

-- View para últimas predições
CREATE OR REPLACE VIEW vw_ultimas_predicoes AS
SELECT 
    p.id,
    p.timestamp_utc,
    p.codigo_wmo,
    COALESCE(e.nome, p.estacao_nome) as estacao_nome,
    e.uf,
    e.latitude,
    e.longitude,
    p.precipitacao_mm,
    p.pressao_estacao_mb,
    p.temperatura_ar_c,
    p.umidade_rel_horaria_pct,
    p.vento_velocidade_ms,
    p.intensidade_predita,
    p.probabilidade_forte,
    p.probabilidade_moderada,
    p.probabilidade_leve,
    p.probabilidade_sem_chuva,
    p.modelo_usado,
    p.created_at
FROM predicoes_intensidade p
LEFT JOIN estacoes e ON p.codigo_wmo = e.codigo_wmo
ORDER BY p.timestamp_utc DESC
LIMIT 1000;

-- View para comparação entre predições e dados reais
CREATE OR REPLACE VIEW vw_comparacao_predicoes AS
SELECT 
    p.timestamp_utc as predicao_timestamp,
    p.codigo_wmo,
    p.intensidade_predita,
    p.probabilidade_forte,
    p.probabilidade_moderada,
    p.probabilidade_leve,
    p.probabilidade_sem_chuva,
    dm.intensidade_chuva as intensidade_real,
    dm.precipitacao_mm as precip_real,
    CASE 
        WHEN p.intensidade_predita = dm.intensidade_chuva THEN 'correto'
        ELSE 'incorreto'
    END as acuracia
FROM predicoes_intensidade p
LEFT JOIN dados_meteorologicos dm 
    ON p.codigo_wmo = dm.codigo_wmo 
    AND ABS(EXTRACT(EPOCH FROM (p.timestamp_utc - dm.timestamp_utc))) < 3600  -- Dentro de 1 hora
WHERE dm.intensidade_chuva IS NOT NULL
ORDER BY p.timestamp_utc DESC;

