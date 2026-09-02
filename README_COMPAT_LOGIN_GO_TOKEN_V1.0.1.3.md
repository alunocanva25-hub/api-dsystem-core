# DSYSTEM SERVER CORE V1.0.1.3 — COMPAT LOGIN GO TOKEN

## Objetivo

Blindar o contrato de login entre o DS STUDIO GO e a DSYSTEM SERVER CORE API.

## Ajustes

- `/api/auth/login` agora retorna `access_token` e também `token`.
- `/api/auth/login` também retorna `company` e `modules` no nível principal.
- `/api/login` retorna múltiplos aliases de token para compatibilidade:
  - `access_token`
  - `token`
  - `jwt`
  - `bearer`
  - `data.access_token`
  - `data.token`
- Criada rota de diagnóstico:
  - `POST /api/debug/login-check`

## Teste recomendado

1. Rodar a API em modo rede com `INICIAR_SERVIDOR_REDE.bat`.
2. Testar no `/docs`:
   - `POST /api/debug/login-check`
   - `POST /api/auth/login`
   - `POST /api/login`
3. Confirmar que as respostas têm `access_token` e `token`.
4. Configurar o GO com `http://IP-DA-MAQUINA:8000`.
