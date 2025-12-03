# Scripts do Projeto

## populate_thingsboard.py

Script para popular o ThingsBoard com dados históricos do INMET.

### Como usar:

1. Certifique-se de que o ThingsBoard está rodando:
   ```bash
   docker logs thingsboard -f
   ```

2. Execute o script:
   ```bash
   python scripts/populate_thingsboard.py
   ```

### O que o script faz:

- Conecta ao ThingsBoard (http://localhost:9090)
- Cria dispositivos IoT para cada estação meteorológica de PE
- Lê os arquivos CSV da pasta `fastapi/app/data/raw`
- Envia os dados como telemetria para os dispositivos
- Configura atributos das estações (nome, latitude, longitude, etc.)

### Credenciais padrão:

- **Usuário**: tenant@thingsboard.org
- **Senha**: tenant
