# DSYSTEM SERVER CORE V1.0.1.5 — EXCLUSÃO LÓGICA GO → STUDIO

Esta versão corrige o contrato de exclusão lógica entre **DS STUDIO GO**, **API CORE** e **DSYSTEM STUDIO**.

## Problema corrigido

Antes, quando o GO excluía um lançamento financeiro, a API mantinha campos como `sync_status` nulos. Assim o DSYSTEM STUDIO não entendia que o lançamento deveria ser cancelado/removido localmente.

## Regra oficial

Quando o GO excluir um registro, a API deve manter o registro e marcar:

```json
{
  "deleted": true,
  "is_deleted": true,
  "deleted_at": "data/hora",
  "status": "cancelado",
  "sync_status": "cancelado",
  "source": "go_mobile",
  "sync_source": "go_mobile",
  "last_source": "go_mobile",
  "desktop_imported": false,
  "pending_desktop_pull": true
}
```

## Fluxo esperado

```txt
GO exclui lançamento
↓
API marca como cancelado
↓
Studio puxa /api/studio/pull/transactions
↓
Studio identifica sync_status=cancelado
↓
Studio aplica exclusão/cancelamento local
```

## Rotas principais

```txt
DELETE /api/transactions/{id}
PATCH /api/transactions/{id}
GET /api/studio/pull/transactions
```

Também foram adicionadas exclusões lógicas para clientes e agendamentos.
