# DSYSTEM SERVER CORE V1.0.0.8 — Admin Empresas/Usuários

Esta versão evolui a base aprovada V1.0.0.6 e adiciona rotas administrativas para o futuro **DSYSTEM HUB**.

## Login local

```json
{
  "username": "master",
  "password": "master123",
  "company_slug": "dsystem-master"
}
```

Depois, use o token em **Authorize** no Swagger:

```txt
Bearer SEU_TOKEN
```

## Rotas principais novas

```txt
GET  /api/admin/overview
GET  /api/admin/companies
POST /api/admin/companies
PUT  /api/admin/companies/{company_id}
GET  /api/admin/companies/{company_id}/config

GET  /api/admin/users
POST /api/admin/users
PUT  /api/admin/users/{user_id}

POST /api/admin/company-modules
POST /api/admin/company-products
POST /api/admin/company-product-modules

GET  /api/admin/sync-logs
GET  /api/admin/audit-logs
```

## Exemplo: configurar DSYSTEM RETAIL para uma empresa

```json
{
  "company_id": 1,
  "product_code": "retail",
  "segment_code": "MARKET",
  "plan_code": "PROFISSIONAL",
  "is_active": true,
  "settings_json": {
    "controlled_by": "DSYSTEM HUB / DSYSTEM SERVER CORE",
    "client_can_choose_segment": false,
    "uses_expiration_control": true,
    "uses_loss_control": true,
    "uses_pdv": true
  }
}
```

## Exemplo: liberar submódulo do RETAIL

```json
{
  "company_id": 1,
  "product_code": "retail",
  "module_code": "retail.pdv",
  "name": "PDV",
  "is_enabled": true,
  "settings_json": {}
}
```

## Diretriz mantida

O cliente final não escolhe o nicho dentro do RETAIL. O segmento é configurado no DSYSTEM HUB / SERVER CORE.
