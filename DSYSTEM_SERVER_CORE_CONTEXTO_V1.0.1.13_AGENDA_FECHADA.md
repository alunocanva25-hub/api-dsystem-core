# DSYSTEM SERVER CORE — CONTEXTO V1.0.1.13 — AGENDA FECHADA

Base anterior: `DSYSTEM_SERVER_CORE_V1.0.1.12_AUTORIDADE_AGENDA_DS_GO`.
Base atual: `DSYSTEM_SERVER_CORE_V1.0.1.13_AGENDA_FECHADA`.

## Regra preservada
DS Go é a autoridade para:
- ativar/desativar a Agenda Online;
- modo fixo/flexível;
- horários fixos.

Studio apenas acompanha esses pontos.

## Alteração V1.0.1.13
A rota pública `/agendamento-publico/{slug}` passa a apresentar uma página HTML clara e responsiva de **Agenda fechada** quando a Agenda Online estiver desativada.

Antes: JSON/404 de indisponibilidade.
Agora: mensagem amigável ao cliente no mesmo link público.

As APIs de busca, disponibilidade e criação continuam bloqueadas enquanto a agenda estiver desativada.

## Deploy Render
Definir `APP_VERSION=1.0.1.13`.

## Coordenação
Usar com:
- DS Go V1.0.0.30;
- Studio patch V7.9.5.109.

## Pendência futura
Sincronização bidirecional de exclusão de agendamentos Studio -> CORE -> Go ainda precisa de etapa própria. GO -> CORE -> Studio já possui fluxo de exclusão lógica preparado.
