# 📊 20 Queries SQL Interativas para Grafana
## Classificação de Intensidade de Chuva - INMET

Todas as queries abaixo são interativas e usam variáveis do Grafana para filtros dinâmicos.

---

## 📈 1. Gráfico de Barras - Distribuição de Intensidade de Chuva

**Título:** Distribuição de Intensidade de Chuva por Classe  
**Tipo:** Bar Chart  
**Interativo:** Sim (usa filtro de tempo do Grafana)

```sql
SELECT 
    intensidade_chuva,
    COUNT(*) as total_registros,
    ROUND(COUNT(*) * 100.0 / NULLIF((
        SELECT COUNT(*) 
        FROM dados_meteorologicos 
        WHERE $__timeFilter(timestamp_utc)
        AND intensidade_chuva IS NOT NULL
    ), 0), 2) as percentual
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY intensidade_chuva
ORDER BY 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

---

## 📈 2. Linha Temporal - Precipitação por Intensidade (Colorida)

**Título:** Série Temporal de Precipitação Colorida por Intensidade  
**Tipo:** Time Series  
**Interativo:** Sim (filtro de tempo + agrupamento por intensidade)

```sql
SELECT 
    timestamp_utc as time,
    precipitacao_mm as value,
    intensidade_chuva
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
ORDER BY timestamp_utc, intensidade_chuva;
```

**Configuração:** Use Transform → Group by → `intensidade_chuva` para colorir por categoria

---

## 📈 3. Gráfico de Barras Agrupadas - Intensidade por Estação

**Título:** Distribuição de Intensidade de Chuva por Estação Meteorológica  
**Tipo:** Bar Chart (agrupado)  
**Interativo:** Sim

**Versão 1: Usando código WMO (recomendado - evita sobreposição)**
```sql
SELECT 
    e.codigo_wmo as estacao,
    dm.intensidade_chuva,
    COUNT(*) as total_registros,
    AVG(dm.precipitacao_mm) as precip_media
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
GROUP BY e.codigo_wmo, dm.intensidade_chuva
ORDER BY e.codigo_wmo,
    CASE dm.intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

**Versão 2: Usando nome completo (se preferir)**
```sql
SELECT 
    LEFT(e.nome, 15) as estacao,
    dm.intensidade_chuva,
    COUNT(*) as total_registros,
    AVG(dm.precipitacao_mm) as precip_media
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
GROUP BY LEFT(e.nome, 15), dm.intensidade_chuva
ORDER BY LEFT(e.nome, 15),
    CASE dm.intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

**Versão 3: Top N estações (para reduzir sobreposição)**
```sql
SELECT 
    e.codigo_wmo as estacao,
    dm.intensidade_chuva,
    COUNT(*) as total_registros,
    AVG(dm.precipitacao_mm) as precip_media
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
  AND e.codigo_wmo IN (
    SELECT codigo_wmo 
    FROM (
      SELECT codigo_wmo, COUNT(*) as total
      FROM dados_meteorologicos
      WHERE $__timeFilter(timestamp_utc)
      GROUP BY codigo_wmo
      ORDER BY total DESC
      LIMIT 10
    ) top_estacoes
  )
GROUP BY e.codigo_wmo, dm.intensidade_chuva
ORDER BY e.codigo_wmo,
    CASE dm.intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

**Configuração no Grafana para evitar sobreposição:**
- **Panel Options** → **Legend**: Configure para "Bottom" ou "Right"
- **Axis** → **Label**: Reduza tamanho da fonte se necessário
- **Bar Chart Options** → **Orientation**: Use "Horizontal" se houver muitas estações
- **Display** → **Rotation**: Rotacione labels se necessário (0°, 45°, 90°)

---

## 📈 4. Heatmap Temporal - Precipitação por Estação e Data

**Título:** Heatmap de Precipitação por Estação e Período  
**Tipo:** Heatmap  
**Interativo:** Sim (filtro de tempo)

```sql
SELECT 
    DATE(dm.timestamp_utc) as time,
    e.codigo_wmo as estacao,
    AVG(dm.precipitacao_mm) as value,
    dm.intensidade_chuva
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
GROUP BY DATE(dm.timestamp_utc), e.codigo_wmo, dm.intensidade_chuva
ORDER BY time, e.codigo_wmo;
```

---

## 📈 5. Gráfico de Linha - Precipitação Média Diária por Intensidade

**Título:** Precipitação Média Diária Agrupada por Intensidade  
**Tipo:** Time Series  
**Interativo:** Sim

```sql
SELECT 
    DATE(timestamp_utc) as time,
    intensidade_chuva,
    AVG(precipitacao_mm) as value,
    MAX(precipitacao_mm) as max_precip,
    MIN(precipitacao_mm) as min_precip
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY DATE(timestamp_utc), intensidade_chuva
ORDER BY time, intensidade_chuva;
```

---

## 📈 6. Gráfico de Área Empilhada -Distribuição Temporal de Intensidades

**Título:** Distribuição Temporal de Intensidades (Área Empilhada)  
**Tipo:** Time Series (Stacked Area)  
**Interativo:** Sim

```sql
SELECT 
    DATE(timestamp_utc) as time,
    intensidade_chuva,
    COUNT(*) as value
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY DATE(timestamp_utc), intensidade_chuva
ORDER BY time,
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

**Configuração:** Panel → Options → Stacking → Normal

---

## 📈 7. Gráfico de Barras Horizontais - Top 10 Estações com Mais Chuva Forte

**Título:** Top 10 Estações com Mais Registros de Chuva Forte  
**Tipo:** Bar Chart (Horizontal)  
**Interativo:** Sim

```sql
SELECT 
    e.nome as estacao,
    COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'forte') as chuva_forte,
    COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'moderada') as chuva_moderada,
    COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'leve') as chuva_leve,
    MAX(dm.precipitacao_mm) as precip_maxima
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
GROUP BY e.nome
HAVING COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'forte') > 0
ORDER BY chuva_forte DESC
LIMIT 10;
```

---

## 📈 8. Gráfico de Linha - Temperatura vs Precipitação por Intensidade

**Título:** Correlação Temperatura e Precipitação por Intensidade  
**Tipo:** Time Series (múltiplas séries)  
**Interativo:** Sim

```sql
SELECT 
    timestamp_utc as time,
    intensidade_chuva,
    AVG(temperatura_ar_c) as temperatura_media,
    AVG(precipitacao_mm) as precipitacao_media,
    AVG(umidade_rel_horaria_pct) as umidade_media
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY timestamp_utc, intensidade_chuva
ORDER BY timestamp_utc;
```

**Configuração:** Use Transform para criar múltiplas séries (temperatura, precipitação, umidade)

---

## 📈 9. Gráfico de Pizza - Percentual de Intensidades

**Título:** Distribuição Percentual de Intensidades de Chuva  
**Tipo:** Pie Chart  
**Interativo:** Sim

```sql
SELECT 
    intensidade_chuva,
    COUNT(*) as value,
    ROUND(COUNT(*) * 100.0 / NULLIF((
        SELECT COUNT(*) 
        FROM dados_meteorologicos 
        WHERE $__timeFilter(timestamp_utc)
        AND intensidade_chuva IS NOT NULL
    ), 0), 2) as percentual
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY intensidade_chuva
ORDER BY 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

---

## 📈 10. Tabela Interativa - Estatísticas Detalhadas por Estação

**Título:** Estatísticas Detalhadas por Estação Meteorológica  
**Tipo:** Table  
**Interativo:** Sim (filtro de tempo)

```sql
SELECT 
    e.codigo_wmo,
    e.nome as estacao,
    e.uf,
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'sem_chuva') as sem_chuva,
    COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'leve') as leve,
    COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'moderada') as moderada,
    COUNT(*) FILTER (WHERE dm.intensidade_chuva = 'forte') as forte,
    ROUND(AVG(dm.precipitacao_mm), 2) as precip_media,
    ROUND(MAX(dm.precipitacao_mm), 2) as precip_maxima,
    ROUND(AVG(dm.temperatura_ar_c), 2) as temp_media,
    ROUND(AVG(dm.umidade_rel_horaria_pct), 2) as umidade_media,
    ROUND(AVG(dm.pressao_estacao_mb), 2) as pressao_media
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
GROUP BY e.codigo_wmo, e.nome, e.uf
ORDER BY total_registros DESC;
```

---

## 📈 11. Gráfico de Barras - Precipitação Total Mensal por Intensidade

**Título:** Precipitação Total Mensal Agrupada por Intensidade  
**Tipo:** Bar Chart  
**Interativo:** Sim

```sql
SELECT 
    DATE_TRUNC('month', timestamp_utc)::DATE as time,
    intensidade_chuva,
    SUM(precipitacao_mm) as value,
    COUNT(*) as total_registros
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY DATE_TRUNC('month', timestamp_utc), intensidade_chuva
ORDER BY time,
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

---

## 📈 12. Gráfico de Linha - Tendência de Intensidade ao Longo do Tempo

**Título:** Tendência de Ocorrência de Intensidades ao Longo do Tempo  
**Tipo:** Time Series  
**Interativo:** Sim

```sql
SELECT 
    DATE(timestamp_utc) as time,
    intensidade_chuva,
    COUNT(*) as ocorrencias,
    ROUND(AVG(precipitacao_mm), 2) as precip_media
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY DATE(timestamp_utc), intensidade_chuva
ORDER BY time, 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

---

## 📈 13. Gráfico de Dispersão - Precipitação vs Umidade por Intensidade

**Título:** Dispersão: Precipitação vs Umidade Relativa por Intensidade  
**Tipo:** Scatter Plot  
**Interativo:** Sim

```sql
SELECT 
    AVG(precipitacao_mm) as x,
    AVG(umidade_rel_horaria_pct) as y,
    intensidade_chuva,
    COUNT(*) as tamanho_bubble
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
  AND precipitacao_mm IS NOT NULL
  AND umidade_rel_horaria_pct IS NOT NULL
GROUP BY DATE(timestamp_utc), intensidade_chuva
ORDER BY intensidade_chuva;
```

**Configuração:** Use campo `tamanho_bubble` para tamanho das bolhas

---

## 📈 14. Gráfico de Barras - Comparação de Variáveis Meteorológicas por Intensidade

**Título:** Comparação de Variáveis Meteorológicas Médias por Intensidade  
**Tipo:** Bar Chart (múltiplas séries)  
**Interativo:** Sim

```sql
SELECT 
    intensidade_chuva,
    ROUND(AVG(temperatura_ar_c), 2) as temperatura,
    ROUND(AVG(umidade_rel_horaria_pct), 2) as umidade,
    ROUND(AVG(pressao_estacao_mb), 2) as pressao,
    ROUND(AVG(vento_velocidade_ms), 2) as vento,
    ROUND(AVG(radiacao_global_kjm2), 2) as radiacao
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY intensidade_chuva
ORDER BY 
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

**Configuração:** Use Transform para criar múltiplas séries

---

## 📈 15. Gráfico de Linha - Precipitação Acumulada por Estação

**Título:** Precipitação Acumulada ao Longo do Tempo por Estação  
**Tipo:** Time Series  
**Interativo:** Sim

```sql
SELECT 
    timestamp_utc as time,
    e.nome as estacao,
    SUM(precipitacao_mm) OVER (
        PARTITION BY e.codigo_wmo 
        ORDER BY timestamp_utc
    ) as precip_acumulada
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
ORDER BY timestamp_utc, e.nome;
```

---

## 📈 16. Gráfico de Barras - Frequência de Intensidades por Hora do Dia

**Título:** Frequência de Intensidades por Hora do Dia  
**Tipo:** Bar Chart  
**Interativo:** Sim

```sql
SELECT 
    EXTRACT(HOUR FROM timestamp_utc) as hora,
    intensidade_chuva,
    COUNT(*) as frequencia,
    ROUND(AVG(precipitacao_mm), 2) as precip_media_hora
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY EXTRACT(HOUR FROM timestamp_utc), intensidade_chuva
ORDER BY hora,
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

---

## 📈 17. Gráfico de Linha - Precipitação Máxima Diária por Intensidade

**Título:** Precipitação Máxima Diária por Intensidade  
**Tipo:** Time Series  
**Interativo:** Sim

```sql
SELECT 
    DATE(timestamp_utc) as time,
    intensidade_chuva,
    MAX(precipitacao_mm) as value,
    MIN(precipitacao_mm) as min_precip,
    AVG(precipitacao_mm) as media_precip
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
  AND intensidade_chuva != 'sem_chuva'
GROUP BY DATE(timestamp_utc), intensidade_chuva
ORDER BY time, intensidade_chuva;
```

---

## 📈 18. Gráfico de Barras - Distribuição de Intensidades por UF

**Título:** Distribuição de Intensidades de Chuva por Estado (UF)  
**Tipo:** Bar Chart  
**Interativo:** Sim

```sql
SELECT 
    e.uf,
    intensidade_chuva,
    COUNT(*) as total_registros,
    ROUND(AVG(precipitacao_mm), 2) as precip_media,
    COUNT(DISTINCT e.codigo_wmo) as num_estacoes
FROM dados_meteorologicos dm
JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
WHERE $__timeFilter(dm.timestamp_utc)
  AND dm.intensidade_chuva IS NOT NULL
GROUP BY e.uf, intensidade_chuva
ORDER BY e.uf,
    CASE intensidade_chuva
        WHEN 'sem_chuva' THEN 1
        WHEN 'leve' THEN 2
        WHEN 'moderada' THEN 3
        WHEN 'forte' THEN 4
    END;
```

---

## 📈 19. Gráfico de Linha - Correlação Vento vs Precipitação por Intensidade

**Título:** Correlação entre Velocidade do Vento e Precipitação por Intensidade  
**Tipo:** Time Series (múltiplas séries)  
**Interativo:** Sim

```sql
SELECT 
    DATE(timestamp_utc) as time,
    intensidade_chuva,
    ROUND(AVG(vento_velocidade_ms), 2) as vento_medio,
    ROUND(AVG(precipitacao_mm), 2) as precip_media,
    ROUND(AVG(vento_rajada_max_ms), 2) as vento_rajada_max
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
  AND intensidade_chuva != 'sem_chuva'
GROUP BY DATE(timestamp_utc), intensidade_chuva
ORDER BY time, intensidade_chuva;
```

---

## 📈 20. Tabela de Resumo - Métricas Principais por Período

**Título:** Resumo de Métricas Principais por Período  
**Tipo:** Table (com múltiplas métricas)  
**Interativo:** Sim

```sql
SELECT 
    DATE(timestamp_utc) as data,
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE intensidade_chuva = 'sem_chuva') as sem_chuva,
    COUNT(*) FILTER (WHERE intensidade_chuva = 'leve') as leve,
    COUNT(*) FILTER (WHERE intensidade_chuva = 'moderada') as moderada,
    COUNT(*) FILTER (WHERE intensidade_chuva = 'forte') as forte,
    ROUND(SUM(precipitacao_mm), 2) as precip_total_dia,
    ROUND(MAX(precipitacao_mm), 2) as precip_max_dia,
    ROUND(AVG(temperatura_ar_c), 2) as temp_media_dia,
    ROUND(AVG(umidade_rel_horaria_pct), 2) as umidade_media_dia,
    COUNT(DISTINCT codigo_wmo) as estacoes_ativas
FROM dados_meteorologicos
WHERE $__timeFilter(timestamp_utc)
  AND intensidade_chuva IS NOT NULL
GROUP BY DATE(timestamp_utc)
ORDER BY data DESC;
```

---

## 🎨 Dicas de Configuração

### Para Time Series:
- Campo de tempo deve ser nomeado como `time`
- Campo de valor deve ser nomeado como `value`
- Use `$__timeFilter()` para filtros temporais

### Para Gráficos Agrupados:
- Use Transform → Group by para agrupar por categoria
- Configure cores diferentes para cada grupo

### Para Tabelas:
- Configure formatação de números (decimais, unidades)
- Adicione cores condicionais (thresholds)

### Para Heatmaps:
- Campo de tempo: `time`
- Campo Y: estação ou categoria
- Campo de valor: `value`

---

## ✅ Checklist de Uso

- [ ] Execute `sql_scripts/04_views_grafana.sql` para criar views auxiliares
- [ ] Verifique se há dados: `SELECT COUNT(*) FROM dados_meteorologicos;`
- [ ] Verifique classificação: `SELECT COUNT(*) FROM dados_meteorologicos WHERE intensidade_chuva IS NOT NULL;`
- [ ] Configure filtro de tempo no dashboard
- [ ] Use Transform quando necessário para agrupar dados
- [ ] Configure cores por categoria de intensidade

---

**Todas as queries são interativas e respondem ao filtro de tempo do Grafana!**

