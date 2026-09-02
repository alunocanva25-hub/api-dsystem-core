# DSYSTEM SERVER CORE V1.0.1.13 — AGENDA FECHADA

## Base
Derivada diretamente da `V1.0.1.12_AUTORIDADE_AGENDA_DS_GO`.

## Alteração exclusiva
Quando a empresa existe, mas a Agenda Online está desativada pelo DS Go, a rota pública:

`/agendamento-publico/{slug}`

não mostra mais JSON/erro escuro de indisponibilidade.

Agora retorna uma página HTML responsiva, clara e no padrão DSYSTEM com:
- `Agenda fechada`;
- nome/marca da empresa;
- mensagem informando que os agendamentos online estão temporariamente fechados;
- orientação para tentar novamente mais tarde ou entrar em contato com a empresa.

O mesmo link volta a funcionar automaticamente quando o DS Go reativar a Agenda Online.

## Preservado
- DS Go continua autoridade para `enabled`, modo e horários fixos;
- Studio continua impedido de sobrescrever esses campos;
- APIs públicas de busca/disponibilidade/criação continuam bloqueadas quando a agenda está desativada;
- multiempresa e `company_slug` preservados;
- ONLINE-UUID, UPSERT e demais funções preservados.

## Render
Após publicar, usar:

`APP_VERSION=1.0.1.13`
