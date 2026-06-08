# DSYSTEM SERVER CORE V1.0.0.8 — Segurança e Permissões

Esta versão evolui a base aprovada V1.0.0.7 adicionando uma matriz inicial de perfis e permissões para preparar o futuro DSYSTEM HUB e os módulos reais.

## Perfis oficiais

- MASTER
- ADMIN
- MANAGER
- OPERATOR
- VIEWER

## Rotas novas

```txt
GET /api/auth/permissions
GET /api/auth/context
GET /api/core/security-standards
```

## Login local

```json
{
  "username": "master",
  "password": "master123",
  "company_slug": "dsystem-master"
}
```

Depois use no Swagger:

```txt
Bearer SEU_TOKEN
```

## Observação de produção

Antes de produção ainda será necessário configurar PostgreSQL, HTTPS, CORS restrito, chave secreta forte, política de senha e backups.
