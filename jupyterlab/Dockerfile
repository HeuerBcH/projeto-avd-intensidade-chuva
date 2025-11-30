FROM jupyter/scipy-notebook:latest

USER root

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

# Instala dependências Python
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    plotly \
    sqlalchemy \
    psycopg2-binary \
    scikit-learn \
    xgboost \
    mlflow \
    boto3 \
    python-dotenv \
    jupyterlab-git

# Configura Jupyter
RUN mkdir -p /home/jovyan/work/notebooks

WORKDIR /home/jovyan/work

# Expõe porta do Jupyter
EXPOSE 8888

CMD ["start-notebook.sh", "--NotebookApp.token=avd2025", "--NotebookApp.password=", "--NotebookApp.allow_origin=*"]






