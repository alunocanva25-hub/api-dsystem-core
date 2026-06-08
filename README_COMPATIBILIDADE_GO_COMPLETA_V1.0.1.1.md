# DSYSTEM SERVER CORE V1.0.1.1 — Compatibilidade GO Completa

Esta versão complementa a V1.0.1.0 com as rotas identificadas no ZIP do DS STUDIO GO V4.0.10.4.36.14.

## Rotas adicionadas

- `GET /api/professionals`
- `POST /api/professionals`
- `PUT /api/professionals/{id}`
- `PATCH /api/professionals/{id}`
- `GET /api/services`
- `POST /api/services`
- `PUT /api/services/{id}`
- `PATCH /api/services/{id}`
- `POST /api/clients`
- `PUT/PATCH /api/clients/{id}`
- `PUT/PATCH /api/appointments/{id}`
- `PUT/PATCH /api/transactions/{id}`

## Teste recomendado

1. Execute `RESETAR_AMBIENTE_LOCAL.bat`.
2. Digite `SIM`.
3. Execute `RUN_LOCAL.bat`.
4. Acesse `http://localhost:8000/docs`.

Login oficial:

```json
{
  "username": "master",
  "password": "master123",
  "company_slug": "dsystem-master"
}
```

Login compatível GO antigo:

```json
{
  "username": "master",
  "password": "123456"
}
```
