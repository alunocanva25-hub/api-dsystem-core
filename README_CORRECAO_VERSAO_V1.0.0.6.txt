DSYSTEM SERVER CORE V1.0.0.6 - CORREÇÃO DE EXIBIÇÃO DE VERSÃO

Correção aplicada:
- RUN_LOCAL.bat exibia V1.0.0.3 no cabeçalho.
- .env.example estava com APP_VERSION=1.0.0.3.

Agora ambos foram corrigidos para 1.0.0.6.

IMPORTANTE:
Se você já tinha rodado a versão anterior, pode existir um arquivo .env antigo na pasta.
Nesse caso, edite o arquivo .env e altere:
APP_VERSION=1.0.0.6

Ou extraia esta versão em uma pasta nova e execute novamente.
