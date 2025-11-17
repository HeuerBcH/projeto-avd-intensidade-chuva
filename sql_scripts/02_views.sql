-- Views úteis para análise

-- View com dados agregados por dia
CREATE OR REPLACE VIEW vw_dados_diarios AS
SELECT 
    codigo_wmo,
    data,
    COUNT(*) as total_registros,
    AVG(precipitacao_mm) as precip_media,
    SUM(precipitacao_mm) as precip_total,
    MAX(precipitacao_mm) as precip_max,
    AVG(temperatura_ar_c) as temp_media,
    MAX(temperatura_ar_c) as temp_max,
    MIN(temperatura_ar_c) as temp_min,
    AVG(umidade_rel_horaria_pct) as umidade_media,
    AVG(pressao_estacao_mb) as pressao_media,
    AVG(vento_velocidade_ms) as vento_medio,
    MAX(vento_rajada_max_ms) as vento_rajada_max
FROM dados_meteorologicos
GROUP BY codigo_wmo, data;

-- View com dados por estação e intensidade de chuva
CREATE OR REPLACE VIEW vw_intensidade_chuva_por_estacao AS
SELECT 
    e.nome as estacao,
    e.uf,
    dm.intensidade_chuva,
    COUNT(*) as total_registros,
    AVG(dm.precipitacao_mm) as precip_media,
    MAX(dm.precipitacao_mm) as precip_max
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE dm.intensidade_chuva IS NOT NULL
GROUP BY e.nome, e.uf, dm.intensidade_chuva
ORDER BY e.nome, dm.intensidade_chuva;

-- View com estatísticas gerais
CREATE OR REPLACE VIEW vw_estatisticas_gerais AS
SELECT 
    COUNT(DISTINCT codigo_wmo) as total_estacoes,
    COUNT(*) as total_registros,
    MIN(timestamp_utc) as data_inicio,
    MAX(timestamp_utc) as data_fim,
    SUM(CASE WHEN precipitacao_mm > 0 THEN 1 ELSE 0 END) as registros_com_chuva,
    AVG(precipitacao_mm) as precip_media_geral,
    MAX(precipitacao_mm) as precip_max_geral
FROM dados_meteorologicos;

