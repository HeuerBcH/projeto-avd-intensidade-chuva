-- Script para atualizar a classificação de intensidade de chuva no banco de dados
-- Baseado nos critérios do problema 7.8:
-- Sem chuva: 0 mm
-- Leve: 0.1 - 2.5 mm/h
-- Moderada: 2.6 - 10 mm/h
-- Forte: > 10 mm/h

-- Atualiza a coluna intensidade_chuva com base na precipitação
UPDATE dados_meteorologicos
SET intensidade_chuva = CASE
    WHEN precipitacao_mm IS NULL OR precipitacao_mm = 0 THEN 'sem_chuva'
    WHEN precipitacao_mm >= 0.1 AND precipitacao_mm <= 2.5 THEN 'leve'
    WHEN precipitacao_mm >= 2.6 AND precipitacao_mm <= 10 THEN 'moderada'
    WHEN precipitacao_mm > 10 THEN 'forte'
    ELSE 'sem_chuva'
END
WHERE intensidade_chuva IS NULL OR intensidade_chuva = '';

-- Verifica a distribuição das classes
SELECT 
    intensidade_chuva,
    COUNT(*) as total_registros,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dados_meteorologicos), 2) as percentual
FROM dados_meteorologicos
GROUP BY intensidade_chuva
ORDER BY 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;






