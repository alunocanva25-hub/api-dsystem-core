# DSYSTEM SERVER CORE V1.0.1.17

Build: `DSYSTEM_SERVER_CORE_V1.0.1.17_TAREFAS_HORARIOS_PERSONALIZADOS`

Atualização incremental sobre a V1.0.1.16.

## Novidades
- tarefas pessoais sincronizadas pelo DS Go;
- bloqueio parcial de capacidade na Agenda Online;
- bloqueio de dia inteiro;
- modo de agenda `personalizado`;
- horários personalizados controlados pelo DS Go.

A página pública não expõe título ou observação das tarefas: usa apenas o bloqueio de capacidade.

## Novos endpoints autenticados
- `GET /api/booking/personal-tasks`
- `POST /api/booking/personal-tasks`

## Autoridade do DS Go
`agendamento_online_horarios_personalizados` passa a fazer parte dos campos que o Studio não pode sobrescrever.

## Preservado
Domingo especial, meses da Agenda Online, link temporário de uso único, identidade/logo, Agenda Fechada, multiempresa, ONLINE-UUID, UPSERT e integrações existentes.

## Integração
- DS Go: `V1.0.0.36`
- Studio: permanece `V7.9.5.110`

## Render
`APP_VERSION=1.0.1.17`
