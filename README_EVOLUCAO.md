# DSYSTEM SERVER CORE V1.0.0.2

## Objetivo da versão

Esta versão evolui a base funcional V1.0.0.1 sem alterar o núcleo que já rodou no Windows.

## Novidades

- Página inicial visual em `/`.
- Rota `/api/core/overview` com resumo do ambiente, banco e totais.
- Rota `/api/sync/ping` para testar canal autenticado de sincronização.
- Rota `/api/sync/studio` como ponto inicial para receber payload do DSYSTEM STUDIO Desktop.
- Listagem de módulos por empresa em `/api/companies/{company_id}/modules`.
- Ativação e desativação de módulo por empresa.
- Documentação de evolução do servidor.

## O que esta versão ainda não faz

- Ainda não grava dados reais de agendamentos, financeiro ou clientes vindos do Desktop.
- Ainda não possui painel administrativo completo.
- Ainda não faz sync bidirecional.
- Ainda não substitui SQLite local dos sistemas desktop.

## Regra de ouro

O DSYSTEM STUDIO Desktop continua sendo o principal neste momento. A API recebe e organiza a base para o futuro, sem quebrar o funcionamento local.

Fluxo alvo:

```text
DSYSTEM STUDIO Desktop
        ↓ sync
DSYSTEM SERVER CORE
        ↓ consumo
DS STUDIO GO
```

## Próxima versão sugerida

V1.0.0.3:

- criar tabelas `customers`, `appointments` e `transactions` no Core;
- criar endpoints reais para receber clientes, agendamentos e financeiro;
- criar regra anti-duplicidade por `external_id` + `company_id` + `module_code`;
- preparar payload compatível com o DS STUDIO GO;
- melhorar o retorno do `/api/auth/me` com empresa e módulos liberados.


## V1.0.0.9 — Admin Empresas/Usuários

Criadas rotas administrativas em `/api/admin` para o futuro DSYSTEM HUB controlar empresas, usuários, produtos contratados, segmentos, planos, módulos liberados, logs de sincronização e auditoria.

Próximo marco sugerido: permissões mais fortes por perfil e preparação de compatibilidade para DS STUDIO GO.
