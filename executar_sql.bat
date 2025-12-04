@echo off
REM Script batch para executar SQL no PostgreSQL via Docker
REM Uso: executar_sql.bat [arquivo.sql]

set ARQUIVO=%~1
if "%ARQUIVO%"=="" set ARQUIVO=sql_scripts/04_views_grafana.sql

echo ========================================
echo   Executando Script SQL
echo ========================================
echo.
echo Arquivo: %ARQUIVO%
echo Container: postgres-inmet
echo Database: inmet_db
echo.

type "%ARQUIVO%" | docker exec -i postgres-inmet psql -U inmet_user -d inmet_db

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Script executado com sucesso!
) else (
    echo.
    echo Erro ao executar script (codigo: %ERRORLEVEL%)
    exit /b %ERRORLEVEL%
)

