# DSYSTEM SERVER CORE V1.0.1.7 — Senha Studio / Reset / Diagnóstico

Esta versão corrige e diagnostica o problema em que o usuário sincronizado pelo DSYSTEM STUDIO aparece na API, mas `password_valid` retorna `false`.

## Novo diagnóstico

`POST /api/debug/login-check` agora retorna também:

```json
{
  "password_present": true,
  "password_scheme": "pbkdf2_sha256",
  "password_length": 88,
  "password_valid": false
}
```

Isso mostra se a senha está presente e qual formato foi armazenado, sem expor a senha/hash.

## Sync de usuários

`POST /api/studio/users/sync` agora retorna:

```json
{
  "password_received": 1,
  "password_updated": 1
}
```

Se `password_received` vier `0`, o DSYSTEM STUDIO não está enviando senha no payload. Nesse caso a API não tem como adivinhar a senha correta.

## Reset administrativo

Nova rota:

`POST /api/admin/users/reset-password-by-username`

Payload:

```json
{
  "username": "RY8854",
  "new_password": "88541025",
  "company_slug": "dsystem-master",
  "must_change_password": false
}
```

Use com token de `master` no botão Authorize do Swagger.
