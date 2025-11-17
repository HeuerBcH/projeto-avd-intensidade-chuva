-- Schema do banco de dados INMET
-- Este script é executado automaticamente na inicialização do PostgreSQL

-- Tabela de estações meteorológicas
CREATE TABLE IF NOT EXISTS estacoes (
    codigo_wmo VARCHAR(10) PRIMARY KEY,
    regiao VARCHAR(2) NOT NULL,
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

-- Índices para melhorar performance de consultas
CREATE INDEX IF NOT EXISTS idx_dados_timestamp ON dados_meteorologicos(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_dados_codigo_data ON dados_meteorologicos(codigo_wmo, data);
CREATE INDEX IF NOT EXISTS idx_dados_intensidade ON dados_meteorologicos(intensidade_chuva);
CREATE INDEX IF NOT EXISTS idx_dados_precipitacao ON dados_meteorologicos(precipitacao_mm);

-- Comentários nas tabelas
COMMENT ON TABLE estacoes IS 'Metadados das estações meteorológicas do INMET';
COMMENT ON TABLE dados_meteorologicos IS 'Dados meteorológicos horários coletados das estações';

COMMENT ON COLUMN dados_meteorologicos.intensidade_chuva IS 'Classificação: sem_chuva, leve, moderada, forte';
COMMENT ON COLUMN dados_meteorologicos.timestamp_utc IS 'Timestamp combinado de data e hora UTC para facilitar consultas temporais';

