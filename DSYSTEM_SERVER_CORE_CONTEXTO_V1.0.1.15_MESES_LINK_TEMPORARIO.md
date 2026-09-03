# DSYSTEM SERVER CORE — CONTEXTO V1.0.1.15

Base anterior: `DSYSTEM_SERVER_CORE_V1.0.1.14_IDENTIDADE_LOGO_AGENDA`.

Versão atual: `DSYSTEM_SERVER_CORE_V1.0.1.15_MESES_LINK_TEMPORARIO`.

## Alterações
- adiciona controle de meses exibidos pela Agenda Online, sob autoridade do DS Go;
- modos: todos, um mês, personalizado;
- `todos` representa janela móvel dos próximos 12 meses;
- disponibilidade rejeita datas fora dos meses autorizados;
- adiciona link temporário/individual de uso único por cliente;
- token temporário armazenado somente como SHA-256;
- após um agendamento concluído com sucesso pelo link, ele é encerrado;
- nova tabela `single_use_booking_links`;
- página de link encerrado preserva identidade/logo da empresa.

## Preservado
- autoridade DS Go para enabled, modo fixo/flexível e horários fixos;
- logo/identidade da V1.0.1.14;
- Agenda Fechada;
- multiempresa por slug;
- ONLINE-UUID e UPSERT;
- login e sincronização Studio/Go;
- endpoints normais da Agenda Online.

## Studio
Nenhum patch novo é necessário. Manter `DSYSTEM_STUDIO_UPDATE_V7.9.5.110_LOGO_AGENDA_ONLINE` como referência atual.

## Deploy
No Render usar `APP_VERSION=1.0.1.15`.

## Integração coordenada
Usar com DS Go `V1.0.0.33`.

## Próxima versão CORE
`V1.0.1.16`.
