#!/bin/bash

# Script para criar o banco thingsboard
# Este script é executado pelo docker-entrypoint-initdb.d

# Conecta ao banco postgres (banco padrão do sistema) para criar outros bancos
# Tenta criar o banco e ignora o erro se já existir
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    CREATE DATABASE thingsboard;
EOSQL

# Sempre retorna sucesso (ignora erro se o banco já existir)
exit 0

