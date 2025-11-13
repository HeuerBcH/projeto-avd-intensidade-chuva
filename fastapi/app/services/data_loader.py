# fastapi/app/services/data_loader.py
from pathlib import Path

def load_local_data():
    """
    Retorna todos os arquivos CSV encontrados em app/data/raw.
    """
    data_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
    if not data_dir.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {data_dir}")

    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em {data_dir}")

    print(f"📂 {len(csv_files)} arquivos encontrados em {data_dir}")
    return csv_files
