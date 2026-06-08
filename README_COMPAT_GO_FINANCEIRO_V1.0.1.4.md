# DSYSTEM SERVER CORE V1.0.1.4 — Compatibilidade Financeira GO

Esta versão é um patch pequeno e focado para corrigir despesas/saldo no DS STUDIO GO.

## Contrato de transação

Cada item de `/api/transactions` passa a devolver aliases compatíveis:

```json
{
  "kind": "saida",
  "type": "saida",
  "tipo": "saida",
  "transaction_type": "saida",
  "amount": 50.0,
  "value": 50.0,
  "valor": 50.0,
  "occurred_at": "2026-06-08T10:00:00",
  "date": "2026-06-08T10:00:00",
  "transaction_date": "2026-06-08T10:00:00"
}
```

## Normalização

Entradas reconhecidas como receita:

- entrada
- receita
- income
- credit/credito
- in
- positivo

Saídas reconhecidas como despesa:

- saida/saída
- despesa
- expense
- debit/debito
- out
- negativo

## Resumo financeiro

Novas rotas:

- `GET /api/transactions/summary`
- `GET /api/financial/summary`

Retorno:

```json
{
  "receitas": 1000.0,
  "despesas": 250.0,
  "saldo": 750.0,
  "income": 1000.0,
  "expenses": 250.0,
  "balance": 750.0
}
```
