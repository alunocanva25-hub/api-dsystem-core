# DSYSTEM SERVER CORE — CONTEXTO V1.0.1.16

Base anterior: `DSYSTEM_SERVER_CORE_V1.0.1.15_MESES_LINK_TEMPORARIO`  
Base atual: `DSYSTEM_SERVER_CORE_V1.0.1.16_DOMINGO_ESPECIAL_DS_GO`  
Próxima versão: `V1.0.1.17`

## Objetivo
Adicionar uma exceção de domingo controlada pelo DS Go sem alterar o comportamento dos demais dias da Agenda Online.

## Novos campos de autoridade do DS Go
- `agendamento_online_domingo_ativo`
- `agendamento_online_domingo_horarios`
- `agendamento_online_domingo_max_clientes`

Esses campos entram em `DS_GO_AUTHORITY_SETTINGS`, portanto o endpoint do DSYSTEM STUDIO não pode sobrescrevê-los.

## Regra de domingo
Quando `agendamento_online_domingo_ativo=true`:
- domingo é considerado dia disponível mesmo que `funcionamento_dias` geral do Studio não contenha domingo;
- a página pública usa exclusivamente `agendamento_online_domingo_horarios`;
- o modo geral fixo/flexível não altera os horários de domingo;
- o limite diário de domingo usa `agendamento_online_domingo_max_clientes`;
- calendário, disponibilidade e criação do agendamento aplicam a mesma regra.

Quando `agendamento_online_domingo_ativo=false`, domingo permanece fechado na Agenda Online.

## Demais dias
Segunda a sábado continuam usando os parâmetros operacionais existentes:
- `funcionamento_dias`;
- `horario_inicio` / `horario_fim`;
- `max_agendamentos_dia`;
- modo/horários fixos definidos pelo DS Go.

## Compatibilidade preservada
Preserva integralmente:
- meses disponíveis da V1.0.1.15;
- link temporário individual de uso único;
- logo/identidade da empresa;
- Agenda Fechada;
- autoridade do DS Go sobre enabled, modo, horários fixos e meses;
- cliente novo/STR;
- ONLINE-UUID;
- UPSERT e isolamento multiempresa;
- login e sincronização Studio/Go.

## Integração
Usar com:
- DS Go `V1.0.0.35`;
- DSYSTEM STUDIO permanece em `V7.9.5.110`.

No Render:
`APP_VERSION=1.0.1.16`

## Teste recomendado
1. No DS Go V35, marcar DOM.
2. Definir domingo com máximo 2 clientes e horários 09:00 e 15:30.
3. Publicar/atualizar Agenda Online.
4. Consultar domingo na página pública e confirmar apenas 09:00 e 15:30.
5. Criar dois agendamentos no mesmo domingo.
6. Confirmar que o terceiro é bloqueado como lotado.
7. Sincronizar o Studio e confirmar que os campos de domingo não são sobrescritos.
