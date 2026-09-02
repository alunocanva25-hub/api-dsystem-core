# DSYSTEM SERVER CORE V1.0.1.9 — Conciliar códigos do Studio

## Objetivo

Completa a correção da V1.0.1.8. Além de preservar `STR0000`, esta versão evita criar um segundo cliente quando o mesmo cadastro já existe na CORE como `CLI-X`/`API_CLIENT_X`/`GO_CLIENT_X`.

## Regra

- Código oficial vindo do DSYSTEM STUDIO: `STRxxxx`.
- `CLI-X` continua válido apenas como ID legado de registros antigos/locais.
- A migração automática é conservadora e exige correspondência forte.
- Agenda e Financeiro são repontados para a nova STR.
- O ID antigo fica registrado em `legacy_external_id`/`legacy_external_ids`.

## Conciliação de base já existente

Usuário MASTER/ADMIN pode chamar:

```text
POST /api/admin/reconcile-client-codes
```

Opcionalmente informar `company_id`.

## Teste recomendado

1. Ter um cliente legado `CLI-3` na CORE.
2. Sincronizar o mesmo cliente pelo Studio com `sigla=STR0000` e mesmo telefone/documento/e-mail.
3. Confirmar que `GET /api/clients` mostra apenas um cliente ativo, com `external_id=STR0000`.
4. Conferir agendamentos/financeiro antes vinculados a `CLI-3`: devem apontar para `STR0000`.
5. Testar um cliente diferente com nome/telefone diferentes: não deve ser mesclado.
