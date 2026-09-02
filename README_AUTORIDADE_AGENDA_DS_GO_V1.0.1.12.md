# DSYSTEM SERVER CORE V1.0.1.12 — AUTORIDADE AGENDA DS GO

Base: `V1.0.1.11_AGENDA_ONLINE_DEPLOY_GUARD`.

## Objetivo
Garantir na própria CORE a regra oficial de autoridade da Agenda Online.

## DS Go é autoridade para
- `enabled` (ativar/desativar);
- `agendamento_online_modo`;
- `agendamento_online_horarios_fixos`.

## DSYSTEM STUDIO
O endpoint `POST /api/studio/public-booking/config` continua aceitando os demais parâmetros operacionais, porém ignora qualquer tentativa do Studio de sobrescrever os três campos acima.

Se ainda não existir configuração da Agenda Online e o Studio sincronizar primeiro, a configuração nasce `enabled=false` até o Master publicar pelo DS Go.

## Preservado
- página pública;
- Company Slug/multiempresa;
- ONLINE-UUID;
- UPSERT sem duplicação;
- clientes/STR;
- serviços/profissionais;
- disponibilidade;
- login e sync existentes.

## Render
Após publicar esta versão, definir `APP_VERSION=1.0.1.12` no Render para a identificação visual coincidir com o build. O marcador `/api/core/deploy-info` também informa o build fixo independentemente da variável.

## Teste de autoridade
1. GO desativa -> CORE `enabled=false`.
2. Studio sincroniza -> continua `false`.
3. GO ativa -> `true`.
4. GO publica modo fixo/horários.
5. Studio sincroniza -> mesmos valores permanecem.
