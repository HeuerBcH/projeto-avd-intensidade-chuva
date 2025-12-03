# 🎯 Guia Completo do Trendz Analytics

Guia consolidado para configurar e usar o Trendz Analytics no projeto de Intensidade de Chuva.

---

## 📋 Índice

1. [Configuração Inicial](#1-configuração-inicial)
2. [Tipos de Views Disponíveis](#2-tipos-de-views-disponíveis)
3. [Criar Visualizações](#3-criar-visualizações)
4. [Queries SQL Prontas](#4-queries-sql-prontas)
5. [Testar Conexão](#5-testar-conexão)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Configuração Inicial

### 1.1 Verificar Serviços

```powershell
# Verificar se Trendz está rodando
docker ps | Select-String trendz

# Verificar se PostgreSQL está rodando
docker ps | Select-String postgres

# Verificar se ThingsBoard está rodando
docker ps | Select-String thingsboard
```

### 1.2 Executar Views SQL

**⚠️ IMPORTANTE:** Execute as views SQL antes de criar visualizações:

```powershell
Get-Content sql_scripts/04_views_trendz.sql | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db
```

**Views criadas:**
- `vw_dados_recentes` - Dados das últimas 24h
- `vw_dados_7_dias` - Dados agregados dos últimos 7 dias
- `vw_distribuicao_intensidade` - Distribuição de classes de intensidade
- `vw_ultimas_predicoes` - Últimas predições do modelo ML
- `vw_comparacao_predicoes` - Comparação entre predições e dados reais

### 1.3 Configurar Datasource PostgreSQL

1. **Acessar Trendz:**
   - URL: **http://localhost:8888**
   - Login: `tenant@thingsboard.org`
   - Senha: `tenant`

2. **Navegar até Data Sources:**
   - Menu lateral → **"Settings"** (ícone de engrenagem)
   - Clique em **"Data Sources"** ou **"Fontes de Dados"**

3. **Adicionar Novo Datasource:**
   - Clique em **"Add new data source"**
   - Preencha os **3 campos obrigatórios**:
     - **URL:** `jdbc:postgresql://localhost:5432/inmet_db`
       - ⚠️ Se acessando do Windows (fora do Docker), use `localhost`
       - Se dentro do Docker, use `postgres`
     - **Login:** `inmet_user`
     - **Password:** `inmet_password`
   - Clique em **"Save"**

### 1.4 Discover Topology (Opcional)

Na primeira vez, você pode ver a tela de "Setup" com botão **"Discover Topology"**:
- Isso descobre dispositivos/assets do ThingsBoard
- Você pode pular isso se não tiver dispositivos ainda
- Não é obrigatório para usar datasource PostgreSQL

---

## 2. Tipos de Views Disponíveis

Quando você clica em **"Add new view"** ou **"Create View"**, você verá estas opções:

### 📊 Visualizações Básicas

1. **Card** - Card simples com informações
2. **Table** - Tabela de dados
3. **Bar** - Gráfico de barras
4. **Line** - Gráfico de linha
5. **Pie** - Gráfico de pizza
6. **Scatter** - Gráfico de dispersão
7. **Heat map** - Mapa de calor
8. **Heat map calendar** - Mapa de calor calendário

### 📈 Visualizações Avançadas

9. **Card with line chart** - Card com gráfico de linha
10. **Anomalies** - Detecção de anomalias
11. **Alarm report** - Relatório de alarmes

---

## 3. Criar Visualizações

### 3.1 Como Criar uma View

**Opção 1: Menu Lateral (Recomendado)**
1. No menu lateral, clique em **"Add new view"** (ícone de +)
2. Escolha o tipo de view (Table, Bar, Line, etc.)
3. Configure a view (veja seção 3.2)

**Opção 2: Dentro de Collections**
1. Clique em **"Collections"** (primeiro item do menu)
2. Crie ou abra uma collection
3. Procure botão **"+"** ou **"Add"** para criar view

### 3.2 Configurar uma View

Após escolher o tipo, você precisa:

1. **Selecionar Data Source:**
   - Escolha o datasource PostgreSQL que você criou

2. **Digitar Query SQL:**
   - Cole uma das queries da seção 4 abaixo
   - Ou escreva sua própria query

3. **Configurar Visualização:**
   - **Para gráficos (Bar, Line, Pie):**
     - Escolha eixo X
     - Escolha eixo Y
     - Escolha cor/agrupamento (opcional)
   - **Para tabelas (Table):**
     - Escolha quais colunas mostrar
     - Configure ordenação (opcional)

4. **Salvar:**
   - Clique em **"Save"** ou **"Apply"**

---

## 4. Queries SQL Prontas

### 4.1 Teste de Conexão (Table)

```sql
SELECT 
    COUNT(*) as total_registros,
    MAX(timestamp_utc) as ultimo_registro
FROM dados_meteorologicos;
```

**Tipo:** Table  
**Use para:** Testar se a conexão está funcionando

---

### 4.2 Gráfico de Barras - Intensidade de Chuva (Bar)

```sql
SELECT 
    intensidade_chuva,
    total_registros,
    percentual,
    precip_media
FROM vw_distribuicao_intensidade
ORDER BY 
    CASE intensidade_chuva
        WHEN 'forte' THEN 1
        WHEN 'moderada' THEN 2
        WHEN 'leve' THEN 3
        WHEN 'sem_chuva' THEN 4
    END;
```

**Tipo:** Bar  
**Configuração:**
- **X-Axis:** `intensidade_chuva`
- **Y-Axis:** `total_registros`
- **Cor:** Por `intensidade_chuva` (opcional)

---

### 4.3 Linha Temporal - Precipitação (Line)

```sql
SELECT 
    timestamp_utc,
    precipitacao_mm,
    intensidade_chuva,
    estacao_nome
FROM vw_dados_recentes
WHERE timestamp_utc >= NOW() - INTERVAL '7 days'
ORDER BY timestamp_utc;
```

**Tipo:** Line  
**Configuração:**
- **X-Axis:** `timestamp_utc`
- **Y-Axis:** `precipitacao_mm`
- **Cor:** Por `intensidade_chuva`
- **Agrupamento:** Por `estacao_nome` (opcional)

---

### 4.4 Tabela - Estatísticas por Estação (Table)

```sql
SELECT 
    estacao_nome,
    uf,
    COUNT(*) as total_registros,
    ROUND(AVG(precipitacao_mm), 2) as precip_media,
    MAX(precipitacao_mm) as precip_max,
    ROUND(AVG(temperatura_ar_c), 2) as temp_media,
    ROUND(AVG(umidade_rel_horaria_pct), 2) as umidade_media
FROM vw_dados_recentes
GROUP BY estacao_nome, uf
ORDER BY precip_media DESC;
```

**Tipo:** Table

---

### 4.5 Gráfico de Pizza - Distribuição (Pie)

```sql
SELECT 
    intensidade_chuva,
    percentual
FROM vw_distribuicao_intensidade;
```

**Tipo:** Pie  
**Configuração:**
- **Categoria:** `intensidade_chuva`
- **Valor:** `percentual`

---

### 4.6 Mapa de Calor - Correlação (Heat map)

```sql
SELECT 
    temperatura_ar_c,
    umidade_rel_horaria_pct,
    pressao_estacao_mb,
    vento_velocidade_ms,
    precipitacao_mm,
    intensidade_chuva
FROM vw_dados_recentes
WHERE timestamp_utc >= NOW() - INTERVAL '7 days';
```

**Tipo:** Heat map  
**Configuração:**
- **Eixo X:** Variáveis meteorológicas
- **Eixo Y:** Valores
- **Cor:** Por `intensidade_chuva`

---

### 4.7 Card - Total de Registros (Card)

```sql
SELECT 
    COUNT(*) as total_registros,
    COUNT(DISTINCT codigo_wmo) as total_estacoes,
    MAX(timestamp_utc) as ultimo_registro
FROM dados_meteorologicos;
```

**Tipo:** Card

---

### 4.8 Card com Gráfico - Precipitação Média (Card with line chart)

```sql
SELECT 
    DATE(timestamp_utc) as data,
    AVG(precipitacao_mm) as precip_media
FROM vw_dados_recentes
WHERE timestamp_utc >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp_utc)
ORDER BY data;
```

**Tipo:** Card with line chart

---

### 4.9 Scatter - Temperatura vs Umidade (Scatter)

```sql
SELECT 
    temperatura_ar_c,
    umidade_rel_horaria_pct,
    intensidade_chuva
FROM vw_dados_recentes
WHERE timestamp_utc >= NOW() - INTERVAL '7 days';
```

**Tipo:** Scatter  
**Configuração:**
- **X-Axis:** `temperatura_ar_c`
- **Y-Axis:** `umidade_rel_horaria_pct`
- **Cor:** Por `intensidade_chuva`

---

### 4.10 Outras Queries Úteis

**Dados Recentes:**
```sql
SELECT * FROM vw_dados_recentes LIMIT 100;
```

**Dados dos Últimos 7 Dias:**
```sql
SELECT * FROM vw_dados_7_dias ORDER BY data DESC;
```

**Últimas Predições:**
```sql
SELECT * FROM vw_ultimas_predicoes LIMIT 50;
```

**Comparação Predições vs Real:**
```sql
SELECT * FROM vw_comparacao_predicoes LIMIT 100;
```

---

## 5. Testar Conexão

### 5.1 Método: Criar View de Teste

**⚠️ IMPORTANTE:** O Trendz não tem botão de "testar conexão". A única forma de testar é **usando o datasource em uma view**.

**Passo a passo:**

1. **Criar View de Teste:**
   - Menu lateral → **"Add new view"**
   - Escolha tipo: **"Table"**

2. **Configurar:**
   - Selecione o datasource PostgreSQL
   - Cole esta query:
   ```sql
   SELECT COUNT(*) as total FROM dados_meteorologicos;
   ```

3. **Verificar:**
   - ✅ **Se aparecer um número:** Conexão funcionando!
   - ❌ **Se aparecer erro:** Veja seção 6 (Troubleshooting)

### 5.2 Query Mínima de Teste

Se a query acima não funcionar, tente esta ainda mais simples:

```sql
SELECT 1 as teste;
```

**Se essa query funcionar, a conexão está OK!**

---

## 6. Troubleshooting

### 6.1 Erro: "Connection refused" ou "Connection timeout"

**Causa:** Trendz não consegue acessar PostgreSQL.

**Solução:**
1. Verifique se PostgreSQL está rodando:
   ```powershell
   docker ps | Select-String postgres
   ```

2. **Se estiver acessando do host Windows**, edite o datasource:
   - URL deve ser: `jdbc:postgresql://localhost:5432/inmet_db`
   - **NÃO use:** `jdbc:postgresql://postgres:5432/inmet_db` (só funciona dentro do Docker)

3. Teste conexão direta:
   ```powershell
   docker exec -it postgres-inmet psql -U inmet_user -d inmet_db -c "SELECT 1;"
   ```

### 6.2 Erro: "Authentication failed" ou "Password authentication failed"

**Causa:** Credenciais incorretas.

**Solução:**
1. Edite o datasource
2. Verifique:
   - **Login:** `inmet_user`
   - **Password:** `inmet_password`
3. Teste credenciais:
   ```powershell
   docker exec -it postgres-inmet psql -U inmet_user -d inmet_db
   ```

### 6.3 Erro: "Table or view does not exist"

**Causa:** Tabelas ou views não existem.

**Solução:**
1. Execute os scripts SQL:
   ```powershell
   Get-Content sql_scripts/01_schema.sql | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db
   Get-Content sql_scripts/04_views_trendz.sql | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db
   ```

2. Verifique se as tabelas existem:
   ```powershell
   docker exec -it postgres-inmet psql -U inmet_user -d inmet_db -c "\dt"
   ```

### 6.4 Erro: "No data available" ou "0 rows"

**Causa:** Não há dados no banco.

**Solução:**
1. Popular ThingsBoard:
   ```powershell
   curl.exe -X POST http://localhost:8000/populate-thingsboard
   ```

2. Coletar dados:
   ```powershell
   curl.exe -X POST http://localhost:8000/ingest-from-thingsboard
   ```

3. Verificar dados:
   ```powershell
   curl.exe -X GET http://localhost:8000/stats
   ```

### 6.5 Não encontro "Add new view"

**Solução:**
1. Procure no menu lateral por **"+"** ou **"Add"**
2. Ou dentro de Collections, procure botão de adicionar
3. Tente criar uma Collection primeiro
4. Verifique se está logado como `tenant@thingsboard.org`
5. Recarregue a página (F5)

---

## 📝 Checklist Completo

### Configuração Inicial
- [ ] Serviços rodando (Trendz, PostgreSQL, ThingsBoard)
- [ ] Views SQL executadas (`04_views_trendz.sql`)
- [ ] Datasource PostgreSQL configurado
- [ ] View de teste criada e funcionando

### Visualizações do Projeto
- [ ] **Bar Chart** - Distribuição de intensidade de chuva
- [ ] **Line Chart** - Precipitação ao longo do tempo (colorida por categoria)
- [ ] **Table** - Estatísticas por estação
- [ ] **Pie Chart** - Distribuição percentual de classes
- [ ] **Heat map** - Correlação entre variáveis (opcional)
- [ ] **Card** - Métricas gerais (opcional)

### Dados
- [ ] ThingsBoard populado
- [ ] Dados coletados do ThingsBoard
- [ ] Dados no PostgreSQL
- [ ] Intensidade de chuva classificada

---

## 🎯 Visualizações Obrigatórias do Projeto

Conforme especificações do projeto, você precisa criar:

1. **Gráfico de Barras por Classe** - Mostrar distribuição de intensidade
2. **Linha Temporal Colorida por Categoria** - Precipitação ao longo do tempo, colorida por intensidade

Use as queries das seções 4.2 e 4.3 acima.

---

## 📚 Referências

- **README Principal:** [README.md](README.md)
- **FastAPI Docs:** http://localhost:8000/docs
- **MLFlow UI:** http://localhost:5000
- **ThingsBoard:** http://localhost:9090
- **JupyterLab:** http://localhost:1010 (token: `avd2025`)

---

## 💡 Dicas Finais

1. **Organize views em Collections** - Crie collections temáticas
2. **Use as views SQL** - Elas já fazem agregações e facilitam as queries
3. **Teste queries primeiro** - Use uma view Table para testar queries antes de criar gráficos
4. **Documente suas views** - Dê nomes descritivos às views criadas
5. **Compartilhe collections** - Se necessário, você pode compartilhar collections com outros usuários

---

**Última atualização:** Baseado na interface real do Trendz Analytics

