# DSYSTEM SERVER CORE V1.0.1.0 — Compatibilidade DS STUDIO GO API

Esta versão cria uma primeira camada de compatibilidade com a API atual do **DS STUDIO GO V2.0.1.4**.

## Objetivo

Permitir que a API CORE comece a absorver as rotas usadas no fluxo atual:

```txt
DSYSTEM STUDIO Desktop -> API -> DS STUDIO GO -> API -> DSYSTEM STUDIO Desktop
```

## Rotas compatíveis adicionadas

```txt
POST /api/login
GET  /api/me
GET  /health
GET  /api/go/compatibility-map

POST /api/studio/users/sync
POST /api/studio/data/sync
POST /api/studio/master-data/sync

POST /api/go/clients
POST /api/go/appointments
POST /api/go/transactions

GET /api/studio/pull/clients
GET /api/studio/pull/appointments
GET /api/studio/pull/transactions
```

## Fontes preservadas

```txt
desktop_sync
go_mobile
api_local
```

## Login de compatibilidade

A rota antiga aceita:

```json
{
  "username": "master",
  "password": "master123"
}
```

Para compatibilidade local com a API antiga do GO, também aceita:

```json
{
  "username": "master",
  "password": "123456"
}
```

## Importante

Como esta versão adiciona campos ao usuário para compatibilidade:

```txt
source
external_id
must_change_password
```

recomenda-se executar:

```bat
RESETAR_AMBIENTE_LOCAL.bat
```

antes de testar.

## Próximos passos

Depois desta versão, o ideal é analisar o ZIP real do **DS STUDIO GO PWA** para ajustar o formato exato dos campos consumidos na interface mobile.
