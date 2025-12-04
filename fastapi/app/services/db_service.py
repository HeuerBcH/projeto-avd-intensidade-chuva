# fastapi/app/services/db_service.py
import os
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

# As variaveis de ambiente sao carregadas automaticamente pelo docker-compose.yml
# via env_file: .env (nao precisa load_dotenv dentro do container)

def get_db_connection():
    """
    Cria e retorna uma conexão com o PostgreSQL.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        return conn
    except Exception as e:
        raise RuntimeError(f"Erro ao conectar com PostgreSQL: {e}")

def test_db_connection():
    """
    Testa a conexão com o banco de dados.
    Retorna True se bem-sucedido, False caso contrário.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        print(f"✅ Conexão com PostgreSQL estabelecida! Versão: {version[0]}")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com PostgreSQL: {e}")
        return False

def insert_estacao(codigo_wmo: str, regiao: str, uf: str, nome: str,
                   latitude: Optional[float] = None, longitude: Optional[float] = None,
                   altitude: Optional[float] = None, data_fundacao: Optional[str] = None):
    """
    Insere ou atualiza uma estação meteorológica.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO estacoes (codigo_wmo, regiao, uf, nome, latitude, longitude, altitude, data_fundacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo_wmo) 
            DO UPDATE SET 
                regiao = EXCLUDED.regiao,
                uf = EXCLUDED.uf,
                nome = EXCLUDED.nome,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                altitude = EXCLUDED.altitude,
                data_fundacao = EXCLUDED.data_fundacao,
                updated_at = CURRENT_TIMESTAMP
        """, (codigo_wmo, regiao, uf, nome, latitude, longitude, altitude, data_fundacao))
        
        conn.commit()
        print(f"✅ Estação {codigo_wmo} ({nome}) inserida/atualizada")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erro ao inserir estação {codigo_wmo}: {e}")
    finally:
        cur.close()
        conn.close()

def insert_dados_meteorologicos_batch(dados: List[Dict]):
    """
    Insere múltiplos registros de dados meteorológicos de uma vez (bulk insert).
    """
    if not dados:
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Prepara os dados para inserção em lote
        values = []
        for d in dados:
            # Usa timestamp_utc se existir, senão combina data e hora
            if 'timestamp_utc' in d and d['timestamp_utc']:
                timestamp_utc = d['timestamp_utc'] if isinstance(d['timestamp_utc'], datetime) else datetime.combine(d['data'], d['hora_utc'])
            else:
                timestamp_utc = datetime.combine(d['data'], d['hora_utc'])
            
            values.append((
                d['codigo_wmo'],
                d['data'],
                d['hora_utc'],
                timestamp_utc,
                d.get('precipitacao_mm'),
                d.get('pressao_estacao_mb'),
                d.get('pressao_max_mb'),
                d.get('pressao_min_mb'),
                d.get('radiacao_global_kjm2'),
                d.get('temperatura_ar_c'),
                d.get('temperatura_orvalho_c'),
                d.get('temperatura_max_c'),
                d.get('temperatura_min_c'),
                d.get('temperatura_orvalho_max_c'),
                d.get('temperatura_orvalho_min_c'),
                d.get('umidade_rel_max_pct'),
                d.get('umidade_rel_min_pct'),
                d.get('umidade_rel_horaria_pct'),
                d.get('vento_direcao_graus'),
                d.get('vento_rajada_max_ms'),
                d.get('vento_velocidade_ms'),
                d.get('intensidade_chuva')
            ))
        
        # Insere em lote usando execute_values para melhor performance
        execute_values(
            cur,
            """
            INSERT INTO dados_meteorologicos (
                codigo_wmo, data, hora_utc, timestamp_utc,
                precipitacao_mm, pressao_estacao_mb, pressao_max_mb, pressao_min_mb,
                radiacao_global_kjm2, temperatura_ar_c, temperatura_orvalho_c,
                temperatura_max_c, temperatura_min_c, temperatura_orvalho_max_c, temperatura_orvalho_min_c,
                umidade_rel_max_pct, umidade_rel_min_pct, umidade_rel_horaria_pct,
                vento_direcao_graus, vento_rajada_max_ms, vento_velocidade_ms,
                intensidade_chuva
            ) VALUES %s
            ON CONFLICT (codigo_wmo, data, hora_utc) 
            DO UPDATE SET
                precipitacao_mm = EXCLUDED.precipitacao_mm,
                pressao_estacao_mb = EXCLUDED.pressao_estacao_mb,
                pressao_max_mb = EXCLUDED.pressao_max_mb,
                pressao_min_mb = EXCLUDED.pressao_min_mb,
                radiacao_global_kjm2 = EXCLUDED.radiacao_global_kjm2,
                temperatura_ar_c = EXCLUDED.temperatura_ar_c,
                temperatura_orvalho_c = EXCLUDED.temperatura_orvalho_c,
                temperatura_max_c = EXCLUDED.temperatura_max_c,
                temperatura_min_c = EXCLUDED.temperatura_min_c,
                temperatura_orvalho_max_c = EXCLUDED.temperatura_orvalho_max_c,
                temperatura_orvalho_min_c = EXCLUDED.temperatura_orvalho_min_c,
                umidade_rel_max_pct = EXCLUDED.umidade_rel_max_pct,
                umidade_rel_min_pct = EXCLUDED.umidade_rel_min_pct,
                umidade_rel_horaria_pct = EXCLUDED.umidade_rel_horaria_pct,
                vento_direcao_graus = EXCLUDED.vento_direcao_graus,
                vento_rajada_max_ms = EXCLUDED.vento_rajada_max_ms,
                vento_velocidade_ms = EXCLUDED.vento_velocidade_ms,
                intensidade_chuva = EXCLUDED.intensidade_chuva
            """,
            values,
            page_size=1000
        )
        
        conn.commit()
        inserted = len(values)
        print(f"✅ {inserted} registros inseridos/atualizados no banco")
        return inserted
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erro ao inserir dados meteorológicos: {e}")
    finally:
        cur.close()
        conn.close()

def get_table_count(table_name: str) -> int:
    """
    Retorna o número de registros em uma tabela.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
            sql.Identifier(table_name)
        ))
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        raise RuntimeError(f"Erro ao contar registros em {table_name}: {e}")
    finally:
        cur.close()
        conn.close()

def insert_predicao_intensidade(
    codigo_wmo: str,
    precipitacao_mm: float,
    pressao_estacao_mb: float,
    temperatura_ar_c: float,
    umidade_rel_horaria_pct: float,
    vento_velocidade_ms: float,
    intensidade_predita: str,
    probabilidade_forte: Optional[float] = None,
    probabilidade_moderada: Optional[float] = None,
    probabilidade_leve: Optional[float] = None,
    probabilidade_sem_chuva: Optional[float] = None,
    modelo_usado: Optional[str] = None,
    estacao_nome: Optional[str] = None
):
    """
    Insere uma predição de intensidade de chuva na tabela predicoes_intensidade.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO predicoes_intensidade (
                timestamp_utc, codigo_wmo, estacao_nome,
                precipitacao_mm, pressao_estacao_mb, temperatura_ar_c,
                umidade_rel_horaria_pct, vento_velocidade_ms,
                intensidade_predita,
                probabilidade_forte, probabilidade_moderada,
                probabilidade_leve, probabilidade_sem_chuva,
                modelo_usado
            ) VALUES (
                CURRENT_TIMESTAMP, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s,
                %s, %s,
                %s, %s,
                %s
            )
        """, (
            codigo_wmo, estacao_nome,
            precipitacao_mm, pressao_estacao_mb, temperatura_ar_c,
            umidade_rel_horaria_pct, vento_velocidade_ms,
            intensidade_predita,
            probabilidade_forte, probabilidade_moderada,
            probabilidade_leve, probabilidade_sem_chuva,
            modelo_usado
        ))
        
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        # Se a tabela não existir, tenta criar
        if "does not exist" in str(e).lower() or "relation" in str(e).lower():
            print("⚠️  Tabela predicoes_intensidade não existe. Execute o script 04_views_trendz.sql")
        raise RuntimeError(f"Erro ao inserir predição: {e}")
    finally:
        cur.close()
        conn.close()

def get_latest_weather_data(limit: int = 100):
    """
    Retorna os dados meteorológicos mais recentes para fazer predições.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                dm.codigo_wmo,
                e.nome as estacao_nome,
                dm.timestamp_utc,
                dm.precipitacao_mm,
                dm.pressao_estacao_mb,
                dm.temperatura_ar_c,
                dm.umidade_rel_horaria_pct,
                dm.vento_velocidade_ms,
                dm.radiacao_global_kjm2
            FROM dados_meteorologicos dm
            JOIN estacoes e ON dm.codigo_wmo = e.codigo_wmo
            WHERE dm.timestamp_utc >= NOW() - INTERVAL '24 hours'
            ORDER BY dm.timestamp_utc DESC
            LIMIT %s
        """, (limit,))
        
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar dados meteorológicos: {e}")
    finally:
        cur.close()
        conn.close()

