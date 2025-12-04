-- Schema do banco de dados INMET
-- Este script é executado automaticamente na inicialização do PostgreSQL

-- Tabela de estações meteorológicas
CREATE TABLE IF NOT EXISTS estacoes (
    codigo_wmo VARCHAR(10) PRIMARY KEY,
    regiao VARCHAR(50) NOT NULL,  -- Aumentado de 2 para 50 (ex: "NORDESTE")
    uf VARCHAR(2) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    altitude DECIMAL(8, 2),
    data_fundacao DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de dados meteorológicos horários
CREATE TABLE IF NOT EXISTS dados_meteorologicos (
    id SERIAL PRIMARY KEY,
    codigo_wmo VARCHAR(10) NOT NULL REFERENCES estacoes(codigo_wmo),
    data DATE NOT NULL,
    hora_utc TIME NOT NULL,
    timestamp_utc TIMESTAMP NOT NULL,
    
    -- Precipitação
    precipitacao_mm DECIMAL(8, 2),
    
    -- Pressão atmosférica
    pressao_estacao_mb DECIMAL(8, 2),
    pressao_max_mb DECIMAL(8, 2),
    pressao_min_mb DECIMAL(8, 2),
    
    -- Radiação
    radiacao_global_kjm2 DECIMAL(10, 2),
    
    -- Temperatura
    temperatura_ar_c DECIMAL(5, 2),
    temperatura_orvalho_c DECIMAL(5, 2),
    temperatura_max_c DECIMAL(5, 2),
    temperatura_min_c DECIMAL(5, 2),
    temperatura_orvalho_max_c DECIMAL(5, 2),
    temperatura_orvalho_min_c DECIMAL(5, 2),
    
    -- Umidade
    umidade_rel_max_pct DECIMAL(5, 2),
    umidade_rel_min_pct DECIMAL(5, 2),
    umidade_rel_horaria_pct DECIMAL(5, 2),
    
    -- Vento
    vento_direcao_graus DECIMAL(6, 2),
    vento_rajada_max_ms DECIMAL(5, 2),
    vento_velocidade_ms DECIMAL(5, 2),
    
    -- Classificação de intensidade de chuva (será preenchida no tratamento)
    intensidade_chuva VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para performance
    CONSTRAINT unique_estacao_data_hora UNIQUE (codigo_wmo, data, hora_utc)
);

-- Tabela de predições ML (Machine Learning)
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

-- Índices para melhorar performance de consultas
CREATE INDEX IF NOT EXISTS idx_dados_timestamp ON dados_meteorologicos(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_dados_codigo_data ON dados_meteorologicos(codigo_wmo, data);
CREATE INDEX IF NOT EXISTS idx_dados_intensidade ON dados_meteorologicos(intensidade_chuva);
CREATE INDEX IF NOT EXISTS idx_dados_precipitacao ON dados_meteorologicos(precipitacao_mm);
CREATE INDEX IF NOT EXISTS idx_predicoes_timestamp ON predicoes_intensidade(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_predicoes_codigo ON predicoes_intensidade(codigo_wmo);
CREATE INDEX IF NOT EXISTS idx_predicoes_intensidade ON predicoes_intensidade(intensidade_predita);

-- Comentários nas tabelas
COMMENT ON TABLE estacoes IS 'Metadados das estações meteorológicas do INMET';
COMMENT ON TABLE dados_meteorologicos IS 'Dados meteorológicos horários coletados das estações';
COMMENT ON TABLE predicoes_intensidade IS 'Predições de intensidade de chuva geradas por modelos ML';

COMMENT ON COLUMN dados_meteorologicos.intensidade_chuva IS 'Classificação: sem_chuva, leve, moderada, forte';
COMMENT ON COLUMN dados_meteorologicos.timestamp_utc IS 'Timestamp combinado de data e hora UTC para facilitar consultas temporais';
COMMENT ON COLUMN predicoes_intensidade.intensidade_predita IS 'Predição ML: sem_chuva, leve, moderada, forte';
COMMENT ON COLUMN predicoes_intensidade.modelo_usado IS 'Nome do modelo ML usado para a predição (ex: GradientBoosting, RandomForest)';

