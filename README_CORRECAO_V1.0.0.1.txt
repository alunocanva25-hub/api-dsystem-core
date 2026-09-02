DSYSTEM SERVER CORE V1.0.0.1 - CORRECAO DE DEPENDENCIAS

Problema corrigido:
- O pacote psycopg2-binary falhava no Windows/Python 3.14.
- Como a instalacao parava nele, pacotes como SQLAlchemy e pydantic-settings nao eram instalados.
- Por isso apareciam erros como:
  ModuleNotFoundError: No module named 'sqlalchemy'
  ModuleNotFoundError: No module named 'pydantic_settings'

O que mudou:
- requirements.txt agora e apenas para uso local com SQLite.
- psycopg2-binary foi removido da instalacao local.
- requirements-postgres.txt foi criado separadamente para producao com PostgreSQL.
- RUN_LOCAL.bat agora atualiza pip/setuptools/wheel antes de instalar.
- RUN_LOCAL.bat roda sem --reload para evitar dependencias extras no Windows.
- Adicionado RESETAR_AMBIENTE_LOCAL.bat para limpar instalacao quebrada.

Como corrigir na sua maquina:
1. Extraia esta nova versao.
2. Execute RESETAR_AMBIENTE_LOCAL.bat e digite SIM.
3. Execute RUN_LOCAL.bat.
4. Acesse: http://localhost:8000/docs
5. Login: master / master123

Observacao:
- Para teste local, use SQLite.
- PostgreSQL entra depois, quando formos subir em Render/VPS/Docker.
