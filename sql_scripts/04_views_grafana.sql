-- ============================================================
-- VIEWS SQL PARA GRAFANA (Dashboards)
-- Classificação de Intensidade de Chuva - Projeto AVD
-- ============================================================

-- Remove views antigas se existirem (para evitar erros de alteração)
DROP VIEW IF EXISTS vw_heatmap_correlacao CASCADE;
DROP VIEW IF EXISTS vw_resumo_geral CASCADE;
DROP VIEW IF EXISTS vw_correlacao_intensidade CASCADE;
DROP VIEW IF EXISTS vw_agregacao_mensal_intensidade CASCADE;
DROP VIEW IF EXISTS vw_dados_recentes_7_dias CASCADE;
DROP VIEW IF EXISTS vw_distribuicao_intensidade_estacao CASCADE;
DROP VIEW IF EXISTS vw_estatisticas_por_estacao CASCADE;
DROP VIEW IF EXISTS vw_temporal_diaria_intensidade CASCADE;
DROP VIEW IF EXISTS vw_grafico_barras_intensidade CASCADE;

-- ============================================================
-- VIEW 1: Gráfico de Barras por Classe de Intensidade
-- Especificação: "Gráfico de barras por classe"
-- ============================================================
CREATE VIEW vw_grafico_barras_intensidade AS
SELECT 
    intensidade_chuva,
    COUNT(*) as total_registros,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dados_meteorologicos WHERE intensidade_chuva IS NOT NULL), 2) as percentual,
    AVG(precipitacao_mm) as precip_media,
    MAX(precipitacao_mm) as precip_max,
    MIN(precipitacao_mm) as precip_min
FROM dados_meteorologicos
WHERE intensidade_chuva IS NOT NULL
GROUP BY intensidade_chuva
ORDER BY 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
        ELSE 5
    END;

-- ============================================================
-- VIEW 2: Linha Temporal Colorida por Categoria
-- Especificação: "linha temporal colorida por categoria"
-- ============================================================
CREATE VIEW vw_temporal_diaria_intensidade AS
SELECT 
    DATE(timestamp_utc) as data,
    intensidade_chuva,
    COUNT(*) as total_registros,
    SUM(precipitacao_mm) as precip_total_dia,
    AVG(precipitacao_mm) as precip_media_dia,
    MAX(precipitacao_mm) as precip_max_dia,
    AVG(temperatura_ar_c) as temp_media,
    AVG(umidade_rel_horaria_pct) as umidade_media,
    AVG(pressao_estacao_mb) as pressao_media,
    AVG(vento_velocidade_ms) as vento_medio
FROM dados_meteorologicos
WHERE intensidade_chuva IS NOT NULL
GROUP BY DATE(timestamp_utc), intensidade_chuva
ORDER BY data DESC, 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;

-- ============================================================
-- VIEW 3: Estatísticas por Estação
-- Especificação: Análise por estação meteorológica
-- ============================================================
CREATE VIEW vw_estatisticas_por_estacao AS
SELECT 
    e.codigo_wmo,
    e.nome as nome_estacao,
    e.uf,
    e.latitude,
    e.longitude,
    COUNT(dm.id) as total_registros,
    MIN(dm.timestamp_utc) as data_inicio,
    MAX(dm.timestamp_utc) as data_fim,
    -- Estatísticas de precipitação
    SUM(CASE WHEN dm.intensidade_chuva != 'sem_chuva' THEN 1 ELSE 0 END) as registros_com_chuva,
    SUM(CASE WHEN dm.intensidade_chuva = 'leve' THEN 1 ELSE 0 END) as registros_chuva_leve,
    SUM(CASE WHEN dm.intensidade_chuva = 'moderada' THEN 1 ELSE 0 END) as registros_chuva_moderada,
    SUM(CASE WHEN dm.intensidade_chuva = 'forte' THEN 1 ELSE 0 END) as registros_chuva_forte,
    AVG(dm.precipitacao_mm) as precip_media,
    MAX(dm.precipitacao_mm) as precip_max,
    SUM(dm.precipitacao_mm) as precip_total,
    -- Estatísticas de temperatura
    AVG(dm.temperatura_ar_c) as temp_media,
    MAX(dm.temperatura_ar_c) as temp_max,
    MIN(dm.temperatura_ar_c) as temp_min,
    -- Estatísticas de umidade
    AVG(dm.umidade_rel_horaria_pct) as umidade_media,
    -- Estatísticas de pressão
    AVG(dm.pressao_estacao_mb) as pressao_media,
    -- Estatísticas de vento
    AVG(dm.vento_velocidade_ms) as vento_medio,
    MAX(dm.vento_rajada_max_ms) as vento_rajada_max
FROM estacoes e
LEFT JOIN dados_meteorologicos dm ON e.codigo_wmo = dm.codigo_wmo
WHERE dm.intensidade_chuva IS NOT NULL
GROUP BY e.codigo_wmo, e.nome, e.uf, e.latitude, e.longitude
ORDER BY e.nome;

-- ============================================================
-- VIEW 4: Distribuição de Intensidade por Estação
-- Para visualização de distribuição por estação
-- ============================================================
CREATE VIEW vw_distribuicao_intensidade_estacao AS
SELECT 
    e.codigo_wmo,
    e.nome as nome_estacao,
    e.uf,
    dm.intensidade_chuva,
    COUNT(*) as total_registros,
    ROUND(COUNT(*) * 100.0 / NULLIF((
        SELECT COUNT(*) 
        FROM dados_meteorologicos dm2 
        WHERE dm2.codigo_wmo = e.codigo_wmo 
        AND dm2.intensidade_chuva IS NOT NULL
    ), 0), 2) as percentual_estacao,
    AVG(dm.precipitacao_mm) as precip_media,
    MAX(dm.precipitacao_mm) as precip_max
FROM estacoes e
JOIN dados_meteorologicos dm ON e.codigo_wmo = dm.codigo_wmo
WHERE dm.intensidade_chuva IS NOT NULL
GROUP BY e.codigo_wmo, e.nome, e.uf, dm.intensidade_chuva
ORDER BY e.nome, 
    CASE dm.intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;

-- ============================================================
-- VIEW 5: Dados Recentes (Últimos 7 dias)
-- Para visualização temporal recente
-- ============================================================
CREATE VIEW vw_dados_recentes_7_dias AS
SELECT 
    dm.timestamp_utc,
    DATE(dm.timestamp_utc) as data,
    TO_CHAR(dm.timestamp_utc, 'HH24:MI') as hora,
    e.nome as nome_estacao,
    e.uf,
    dm.intensidade_chuva,
    dm.precipitacao_mm,
    dm.temperatura_ar_c,
    dm.umidade_rel_horaria_pct,
    dm.pressao_estacao_mb,
    dm.vento_velocidade_ms,
    dm.radiacao_global_kjm2
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE dm.timestamp_utc >= CURRENT_DATE - INTERVAL '7 days'
  AND dm.intensidade_chuva IS NOT NULL
ORDER BY dm.timestamp_utc DESC;

-- ============================================================
-- VIEW 6: Agregação Mensal de Intensidade
-- Para análise de tendências mensais
-- ============================================================
CREATE VIEW vw_agregacao_mensal_intensidade AS
SELECT 
    DATE_TRUNC('month', timestamp_utc)::DATE as mes,
    intensidade_chuva,
    COUNT(*) as total_registros,
    SUM(precipitacao_mm) as precip_total_mes,
    AVG(precipitacao_mm) as precip_media_mes,
    MAX(precipitacao_mm) as precip_max_mes,
    COUNT(DISTINCT codigo_wmo) as num_estacoes
FROM dados_meteorologicos
WHERE intensidade_chuva IS NOT NULL
GROUP BY DATE_TRUNC('month', timestamp_utc), intensidade_chuva
ORDER BY mes DESC, 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;

-- ============================================================
-- VIEW 7: Correlação entre Variáveis e Intensidade
-- Para análise de correlação
-- ============================================================
CREATE VIEW vw_correlacao_intensidade AS
SELECT 
    intensidade_chuva,
    COUNT(*) as total_registros,
    AVG(temperatura_ar_c) as temp_media,
    AVG(umidade_rel_horaria_pct) as umidade_media,
    AVG(pressao_estacao_mb) as pressao_media,
    AVG(vento_velocidade_ms) as vento_medio,
    AVG(radiacao_global_kjm2) as radiacao_media,
    AVG(precipitacao_mm) as precip_media
FROM dados_meteorologicos
WHERE intensidade_chuva IS NOT NULL
GROUP BY intensidade_chuva
ORDER BY 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;

-- ============================================================
-- VIEW 8: Resumo Geral (Para Cards/Métricas)
-- ============================================================
CREATE VIEW vw_resumo_geral AS
SELECT 
    COUNT(DISTINCT codigo_wmo) as total_estacoes,
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE intensidade_chuva IS NOT NULL) as registros_classificados,
    MIN(timestamp_utc) as data_inicio,
    MAX(timestamp_utc) as data_fim,
    SUM(CASE WHEN intensidade_chuva = 'sem_chuva' THEN 1 ELSE 0 END) as total_sem_chuva,
    SUM(CASE WHEN intensidade_chuva = 'leve' THEN 1 ELSE 0 END) as total_leve,
    SUM(CASE WHEN intensidade_chuva = 'moderada' THEN 1 ELSE 0 END) as total_moderada,
    SUM(CASE WHEN intensidade_chuva = 'forte' THEN 1 ELSE 0 END) as total_forte,
    AVG(precipitacao_mm) as precip_media_geral,
    MAX(precipitacao_mm) as precip_max_geral,
    AVG(temperatura_ar_c) as temp_media_geral,
    AVG(umidade_rel_horaria_pct) as umidade_media_geral
FROM dados_meteorologicos;

-- ============================================================
-- VIEW 9: Dados para Heatmap (Correlação)
-- Para visualização de mapa de calor
-- ============================================================
CREATE VIEW vw_heatmap_correlacao AS
SELECT 
    codigo_wmo,
    DATE(timestamp_utc) as data,
    intensidade_chuva,
    AVG(precipitacao_mm) as precip_media,
    AVG(temperatura_ar_c) as temp_media,
    AVG(umidade_rel_horaria_pct) as umidade_media,
    AVG(pressao_estacao_mb) as pressao_media,
    AVG(vento_velocidade_ms) as vento_medio
FROM dados_meteorologicos
WHERE intensidade_chuva IS NOT NULL
GROUP BY codigo_wmo, DATE(timestamp_utc), intensidade_chuva
ORDER BY data DESC, codigo_wmo;

-- ============================================================
-- COMENTÁRIOS NAS VIEWS
-- ============================================================
COMMENT ON VIEW vw_grafico_barras_intensidade IS 'Gráfico de barras por classe de intensidade de chuva';
COMMENT ON VIEW vw_temporal_diaria_intensidade IS 'Linha temporal diária colorida por categoria de intensidade';
COMMENT ON VIEW vw_estatisticas_por_estacao IS 'Estatísticas detalhadas por estação meteorológica';
COMMENT ON VIEW vw_distribuicao_intensidade_estacao IS 'Distribuição de intensidade de chuva por estação';
COMMENT ON VIEW vw_dados_recentes_7_dias IS 'Dados dos últimos 7 dias para visualização temporal';
COMMENT ON VIEW vw_agregacao_mensal_intensidade IS 'Agregação mensal de intensidade de chuva';
COMMENT ON VIEW vw_correlacao_intensidade IS 'Correlação entre variáveis meteorológicas e intensidade';
COMMENT ON VIEW vw_resumo_geral IS 'Resumo geral para cards e métricas principais';
COMMENT ON VIEW vw_heatmap_correlacao IS 'Dados para visualização de heatmap de correlação';

