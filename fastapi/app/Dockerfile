# fastapi/app/Dockerfile
FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários
COPY . /app

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pela API
EXPOSE 8000

# Comando para rodar o servidor FastAPI
CMD ["uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
