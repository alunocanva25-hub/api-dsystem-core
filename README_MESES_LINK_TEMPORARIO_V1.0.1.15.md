# DSYSTEM SERVER CORE V1.0.1.15 — MESES + LINK TEMPORÁRIO

## Escopo
Atualização incremental sobre a V1.0.1.14, preservando Agenda Online, identidade/logo, Agenda Fechada, autoridade do DS Go, login, clientes, serviços, profissionais e sincronização.

## Autoridade do DS Go — meses da Agenda Online
A CORE passa a aceitar como campos de autoridade do DS Go:
- `agendamento_online_meses_modo`: `todos`, `um` ou `personalizado`;
- `agendamento_online_meses`: CSV de meses `1..12`.

A página pública filtra o calendário por esses meses. Em `todos`, trabalha com a janela móvel dos próximos 12 meses, evitando exibir meses já passados do ano corrente.

## Link temporário por cliente — 1 uso
Novo endpoint autenticado:

`POST /api/booking/temporary-links`

Payload:
```json
{"client_ref":"STR0001"}
```

Retorna uma URL individual no formato:

`/agendamento-publico/{slug}/t/{token}`

Regras:
- o link é vinculado a um cliente já sincronizado com a CORE;
- o token bruto nunca é salvo no banco; somente SHA-256;
- um novo link temporário invalida links temporários anteriores ainda não usados para o mesmo cliente;
- o link pode ser aberto antes da reserva, mas permite concluir somente um agendamento;
- após o primeiro agendamento confirmado com sucesso, o link é desativado e passa a mostrar `Link encerrado`;
- o cliente fica pré-identificado e não pode trocar sua identidade no link individual;
- em falha de criação do agendamento, a reserva do token é liberada para nova tentativa.

## Banco
Nova tabela: `single_use_booking_links`.

Na arquitetura SQLite atual ela é criada automaticamente pelo `Base.metadata.create_all()` executado no fluxo de inicialização do banco.

## Deploy Render
Atualizar a aplicação e definir:

`APP_VERSION=1.0.1.15`

Não é necessário alterar Cloudflare, domínio ou Studio para esta atualização.

## Testes mínimos
1. Publicar `todos` e conferir calendário dos próximos 12 meses.
2. Publicar `um` e confirmar que somente o mês selecionado aparece.
3. Publicar `personalizado` e confirmar somente os meses marcados.
4. Gerar link temporário para um cliente sincronizado.
5. Abrir o link e realizar um agendamento.
6. Reabrir a mesma URL e confirmar `Link encerrado`.
7. Confirmar que o link normal continua reutilizável.
