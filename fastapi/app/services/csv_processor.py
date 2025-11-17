# fastapi/app/services/csv_processor.py
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, time
import numpy as np

def parse_inmet_csv(file_path: Path) -> Dict:
    """
    Processa um arquivo CSV do INMET e retorna os dados estruturados.
    
    Retorna um dicionário com:
    - estacao: metadados da estação
    - dados: lista de registros meteorológicos
    """
    # Lê o arquivo com encoding apropriado (tenta diferentes encodings)
    lines = None
    encodings = ['latin-1', 'iso-8859-1', 'windows-1252', 'utf-8']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                lines = f.readlines()
                break
        except Exception as e:
            continue
    
    if lines is None:
        raise ValueError(f"Não foi possível ler o arquivo {file_path.name} com nenhum encoding testado")
    
    # Extrai metadados do cabeçalho
    estacao_info = {}
    header_line = None
    
    for i, line in enumerate(lines):
        if line.startswith('REGIAO:'):
            estacao_info['regiao'] = line.split(';')[1].strip()
        elif line.startswith('UF:'):
            estacao_info['uf'] = line.split(';')[1].strip()
        elif line.startswith('ESTACAO:'):
            estacao_info['nome'] = line.split(';')[1].strip()
        elif line.startswith('CODIGO (WMO):'):
            estacao_info['codigo_wmo'] = line.split(';')[1].strip()
        elif line.startswith('LATITUDE:'):
            lat_str = line.split(';')[1].strip().replace(',', '.')
            estacao_info['latitude'] = float(lat_str) if lat_str else None
        elif line.startswith('LONGITUDE:'):
            lon_str = line.split(';')[1].strip().replace(',', '.')
            estacao_info['longitude'] = float(lon_str) if lon_str else None
        elif line.startswith('ALTITUDE:'):
            alt_str = line.split(';')[1].strip().replace(',', '.')
            estacao_info['altitude'] = float(alt_str) if alt_str else None
        elif line.startswith('DATA DE FUNDACAO:'):
            fundacao_str = line.split(';')[1].strip()
            estacao_info['data_fundacao'] = fundacao_str if fundacao_str else None
        elif line.startswith('Data;'):
            header_line = i
            break
    
    if not header_line:
        raise ValueError(f"Não foi possível encontrar o cabeçalho dos dados em {file_path.name}")
    
    # Lê os dados usando pandas, pulando as linhas de metadados
    # Tenta diferentes encodings
    df = None
    encodings = ['latin-1', 'iso-8859-1', 'windows-1252', 'utf-8']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                sep=';',
                skiprows=header_line,
                encoding=encoding,
                on_bad_lines='skip',
                low_memory=False
            )
            break
        except Exception as e:
            continue
    
    if df is None:
        raise ValueError(f"Não foi possível ler o CSV {file_path.name} com nenhum encoding testado")
    
    # Limpa nomes de colunas
    df.columns = df.columns.str.strip()
    
    # Processa os dados
    dados = []
    
    for _, row in df.iterrows():
        try:
            # Data e hora
            data_str = str(row.get('Data', '')).strip()
            hora_str = str(row.get('Hora UTC', '')).strip().replace(' UTC', '').replace('UTC', '').strip()
            
            if not data_str or not hora_str or data_str == 'nan' or hora_str == 'nan':
                continue
            
            # Converte data
            try:
                data = pd.to_datetime(data_str, format='%Y/%m/%d').date()
            except:
                try:
                    data = pd.to_datetime(data_str, format='%Y-%m-%d').date()
                except:
                    continue
            
            # Converte hora (formato: 0000, 0100, etc.)
            hora_match = re.match(r'(\d{2})(\d{2})', hora_str)
            if hora_match:
                hora = time(int(hora_match.group(1)), int(hora_match.group(2)))
            else:
                continue
            
            # Função auxiliar para converter valores
            def parse_value(val, default=None):
                if pd.isna(val) or val == '' or str(val).strip() == '':
                    return default
                try:
                    val_str = str(val).strip().replace(',', '.')
                    if val_str == '' or val_str.lower() in ['nan', 'none', 'null']:
                        return default
                    return float(val_str)
                except:
                    return default
            
            # Extrai valores das colunas (tenta diferentes nomes possíveis)
            registro = {
                'codigo_wmo': estacao_info['codigo_wmo'],
                'data': data,
                'hora_utc': hora,
                'precipitacao_mm': parse_value(row.get('PRECIPITAÇÃO TOTAL, HORÁRIO (mm)', 
                                                       row.get('PRECIPITACAO TOTAL, HORARIO (mm)', None))),
                'pressao_estacao_mb': parse_value(row.get('PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)',
                                                           row.get('PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)', None))),
                'pressao_max_mb': parse_value(row.get('PRESSÃO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB)',
                                                      row.get('PRESSAO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB)', None))),
                'pressao_min_mb': parse_value(row.get('PRESSÃO ATMOSFERICA MIN. NA HORA ANT. (AUT) (mB)',
                                                      row.get('PRESSAO ATMOSFERICA MIN. NA HORA ANT. (AUT) (mB)', None))),
                'radiacao_global_kjm2': parse_value(row.get('RADIACAO GLOBAL (Kj/m²)',
                                                           row.get('RADIACAO GLOBAL (Kj/m2)', None))),
                'temperatura_ar_c': parse_value(row.get('TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)',
                                                        row.get('TEMPERATURA DO AR - BULBO SECO, HORARIA (C)', None))),
                'temperatura_orvalho_c': parse_value(row.get('TEMPERATURA DO PONTO DE ORVALHO (°C)',
                                                            row.get('TEMPERATURA DO PONTO DE ORVALHO (C)', None))),
                'temperatura_max_c': parse_value(row.get('TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)',
                                                        row.get('TEMPERATURA MAXIMA NA HORA ANT. (AUT) (C)', None))),
                'temperatura_min_c': parse_value(row.get('TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)',
                                                        row.get('TEMPERATURA MINIMA NA HORA ANT. (AUT) (C)', None))),
                'temperatura_orvalho_max_c': parse_value(row.get('TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT) (°C)',
                                                                 row.get('TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT) (C)', None))),
                'temperatura_orvalho_min_c': parse_value(row.get('TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (°C)',
                                                                row.get('TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (C)', None))),
                'umidade_rel_max_pct': parse_value(row.get('UMIDADE REL. MAX. NA HORA ANT. (AUT) (%)',
                                                           row.get('UMIDADE REL. MAX. NA HORA ANT. (AUT) (%)', None))),
                'umidade_rel_min_pct': parse_value(row.get('UMIDADE REL. MIN. NA HORA ANT. (AUT) (%)',
                                                           row.get('UMIDADE REL. MIN. NA HORA ANT. (AUT) (%)', None))),
                'umidade_rel_horaria_pct': parse_value(row.get('UMIDADE RELATIVA DO AR, HORARIA (%)',
                                                              row.get('UMIDADE RELATIVA DO AR, HORARIA (%)', None))),
                'vento_direcao_graus': parse_value(row.get('VENTO, DIREÇÃO HORARIA (gr) (° (gr))',
                                                          row.get('VENTO, DIRECAO HORARIA (gr)', None))),
                'vento_rajada_max_ms': parse_value(row.get('VENTO, RAJADA MAXIMA (m/s)',
                                                           row.get('VENTO, RAJADA MAXIMA (m/s)', None))),
                'vento_velocidade_ms': parse_value(row.get('VENTO, VELOCIDADE HORARIA (m/s)',
                                                          row.get('VENTO, VELOCIDADE HORARIA (m/s)', None))),
            }
            
            dados.append(registro)
        except Exception as e:
            # Ignora linhas com erro e continua
            continue
    
    return {
        'estacao': estacao_info,
        'dados': dados
    }

