# DSYSTEM SERVER CORE V1.0.0.6 — RETAIL, Segmentos e Planos

Esta versão prepara a API CORE para o **DSYSTEM RETAIL — Gestão inteligente para o varejo.**

## Decisão arquitetural

O cliente final **não escolhe** o nicho/segmento dentro do sistema.
Quem define isso é o **DSYSTEM HUB / DSYSTEM SERVER CORE** no cadastro da empresa.

## Alteração principal

Sai do padrão oficial:

```txt
pousada — Gestão Pousada
```

Entra no padrão oficial:

```txt
retail — DSYSTEM RETAIL
```

## Segmentos iniciais do RETAIL

```txt
MARKET        Mercadinho / Supermercado
CONVENIENCE   Conveniência
CONSTRUCTION  Material de construção
GENERAL_STORE Loja geral
```

## Planos iniciais

```txt
BASICO
PROFISSIONAL
PREMIUM
ENTERPRISE
```

## Rotas novas

```txt
GET /api/core/retail-standards
GET /api/core/products
GET /api/core/segments
GET /api/core/plans
GET /api/core/company-product-config
```

## Configuração padrão para teste local

```txt
company_slug: dsystem-master
product_code: retail
segment_code: MARKET
plan_code: PROFISSIONAL
```

## Como testar

1. Execute `RESETAR_AMBIENTE_LOCAL.bat` para criar as novas tabelas limpas.
2. Digite `SIM`.
3. Execute `RUN_LOCAL.bat`.
4. Acesse `http://localhost:8000/docs`.
5. Teste `GET /api/core/company-product-config`.
