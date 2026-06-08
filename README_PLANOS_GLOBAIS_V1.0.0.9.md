# DSYSTEM SERVER CORE V1.0.0.9 — Planos Globais

Nesta versão, o controle de planos passa a ser global para todo o ecossistema DSYSTEM.

## Regra oficial

Os planos não pertencem somente ao DSYSTEM RETAIL. Eles podem ser aplicados a qualquer produto:

- DSYSTEM STUDIO
- DS STUDIO GO
- DSYSTEM AR
- DSYSTEM-AR-PAINEL
- DSYSTEM RETAIL
- PulseLab
- DSYSTEM VISION
- DSYSTEM BIKE
- Inventário
- WinThor Tools

## Planos oficiais

- TRIAL — Teste
- STARTER — Inicial
- BASIC — Básico
- PRO — Profissional
- BUSINESS — Empresarial
- ENTERPRISE — Enterprise

## Status oficiais

- TRIAL
- ACTIVE
- SUSPENDED
- CANCELLED
- EXPIRED

## Controle pelo HUB

O DSYSTEM HUB poderá futuramente:

- ativar produto/plano;
- iniciar plano de teste;
- definir data final do trial;
- trocar plano;
- suspender acesso;
- cancelar produto contratado;
- expirar plano.

## Rotas novas

```txt
GET /api/core/plan-standards
GET /api/admin/plans
PATCH /api/admin/company-products/{company_product_id}/plan
```

## Teste local

Após extrair a versão, recomenda-se executar:

```bat
RESETAR_AMBIENTE_LOCAL.bat
RUN_LOCAL.bat
```

Login local:

```json
{
  "username": "master",
  "password": "master123",
  "company_slug": "dsystem-master"
}
```
