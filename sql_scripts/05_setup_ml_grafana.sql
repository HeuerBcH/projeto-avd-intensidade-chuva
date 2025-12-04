-- ============================================================
-- Script de Setup ML para Grafana
-- Cria tabela de predições e views ML se não existirem
-- Execute este script após atualizar o schema
-- ============================================================

-- Cria tabela de predições ML se não existir
CREATE TABLE IF NOT EXISTS predicoes_intensidade (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    codigo_wmo VARCHAR(10),
    estacao_nome VARCHAR(100),
    -- Dados de entrada para o modelo
    precipitacao_mm DECIMAL(8, 2),
    pressao_estacao_mb DECIMAL(8, 2),
    temperatura_ar_c DECIMAL(5, 2),
    umidade_rel_horaria_pct DECIMAL(5, 2),
    vento_velocidade_ms DECIMAL(5, 2),
    -- Resultado da predição ML
    intensidade_predita VARCHAR(20) NOT NULL,
    probabilidade_forte DECIMAL(5, 4),
    probabilidade_moderada DECIMAL(5, 4),
    probabilidade_leve DECIMAL(5, 4),
    probabilidade_sem_chuva DECIMAL(5, 4),
    modelo_usado VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cria índices se não existirem
CREATE INDEX IF NOT EXISTS idx_predicoes_timestamp ON predicoes_intensidade(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_predicoes_codigo ON predicoes_intensidade(codigo_wmo);
CREATE INDEX IF NOT EXISTS idx_predicoes_intensidade ON predicoes_intensidade(intensidade_predita);

-- Remove views antigas se existirem (para recriar)
DROP VIEW IF EXISTS vw_predicoes_ml CASCADE;
DROP VIEW IF EXISTS vw_comparacao_ml_sql CASCADE;
DROP VIEW IF EXISTS vw_estatisticas_predicoes_ml CASCADE;

-- ============================================================
-- VIEW 10: Predições ML (Machine Learning)
-- ============================================================
CREATE VIEW vw_predicoes_ml AS
SELECT 
    id,
    timestamp_utc as time,
    codigo_wmo,
    estacao_nome,
    precipitacao_mm,
    pressao_estacao_mb,
    temperatura_ar_c,
    umidade_rel_horaria_pct,
    vento_velocidade_ms,
    intensidade_predita,
    probabilidade_forte,
    probabilidade_moderada,
    probabilidade_leve,
    probabilidade_sem_chuva,
    modelo_usado,
    created_at
FROM predicoes_intensidade
ORDER BY timestamp_utc DESC;

-- ============================================================
-- VIEW 11: Comparação ML vs Classificação SQL
-- ============================================================
CREATE VIEW vw_comparacao_ml_sql AS
SELECT 
    dm.timestamp_utc as time,
    dm.codigo_wmo,
    e.nome as estacao_nome,
    dm.precipitacao_mm,
    dm.intensidade_chuva as classificacao_sql,
    pi.intensidade_predita as classificacao_ml,
    CASE 
        WHEN dm.intensidade_chuva = pi.intensidade_predita THEN 'match'
        ELSE 'diferenca'
    END as status_comparacao,
    pi.probabilidade_forte,
    pi.probabilidade_moderada,
    pi.probabilidade_leve,
    pi.probabilidade_sem_chuva,
    pi.modelo_usado
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
LEFT JOIN predicoes_intensidade pi ON 
    dm.codigo_wmo = pi.codigo_wmo 
    AND DATE(dm.timestamp_utc) = DATE(pi.timestamp_utc)
    AND EXTRACT(HOUR FROM dm.timestamp_utc) = EXTRACT(HOUR FROM pi.timestamp_utc)
WHERE dm.intensidade_chuva IS NOT NULL
ORDER BY dm.timestamp_utc DESC;

-- ============================================================
-- VIEW 12: Estatísticas de Predições ML
-- ============================================================
CREATE VIEW vw_estatisticas_predicoes_ml AS
SELECT 
    COUNT(*) as total_predicoes,
    COUNT(DISTINCT codigo_wmo) as estacoes_com_predicoes,
    MIN(timestamp_utc) as primeira_predicao,
    MAX(timestamp_utc) as ultima_predicao,
    SUM(CASE WHEN intensidade_predita = 'sem_chuva' THEN 1 ELSE 0 END) as predicoes_sem_chuva,
    SUM(CASE WHEN intensidade_predita = 'leve' THEN 1 ELSE 0 END) as predicoes_leve,
    SUM(CASE WHEN intensidade_predita = 'moderada' THEN 1 ELSE 0 END) as predicoes_moderada,
    SUM(CASE WHEN intensidade_predita = 'forte' THEN 1 ELSE 0 END) as predicoes_forte,
    COUNT(DISTINCT modelo_usado) as modelos_utilizados,
    AVG(probabilidade_forte) as prob_media_forte,
    AVG(probabilidade_moderada) as prob_media_moderada,
    AVG(probabilidade_leve) as prob_media_leve,
    AVG(probabilidade_sem_chuva) as prob_media_sem_chuva
FROM predicoes_intensidade;

-- Comentários
COMMENT ON TABLE predicoes_intensidade IS 'Predições de intensidade de chuva geradas por modelos ML';
COMMENT ON VIEW vw_predicoes_ml IS 'Predições de intensidade geradas por modelos de Machine Learning';
COMMENT ON VIEW vw_comparacao_ml_sql IS 'Comparação entre classificação SQL (regras) e predições ML';
COMMENT ON VIEW vw_estatisticas_predicoes_ml IS 'Estatísticas gerais das predições ML';

