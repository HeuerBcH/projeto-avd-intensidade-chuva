FROM python:3.10-slim

WORKDIR /app

# Copiar dependências e instalar
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte da aplicação
COPY ./app /app

# Expor a porta do FastAPI
EXPOSE 8000

# Comando para rodar o servidor
CMD ["uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "8000"]
