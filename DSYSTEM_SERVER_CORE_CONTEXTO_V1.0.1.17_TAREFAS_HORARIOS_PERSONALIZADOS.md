# DSYSTEM SERVER CORE — CONTEXTO V1.0.1.17

Base anterior: `DSYSTEM_SERVER_CORE_V1.0.1.16_DOMINGO_ESPECIAL_DS_GO`  
Base atual: `DSYSTEM_SERVER_CORE_V1.0.1.17_TAREFAS_HORARIOS_PERSONALIZADOS`  
Próxima versão: `V1.0.1.18`

## Objetivo
Dar suporte servidor às duas novidades do DS Go V1.0.0.36:
1. `Tarefa pessoal`, capaz de reservar parte da capacidade ou bloquear o dia inteiro;
2. modo de horários `Personalizado`, com horários manuais definidos pelo DS Go.

## 1. Tarefas pessoais
Nova tabela:
`public_booking_personal_tasks`

Cada tarefa possui:
- `company_id`;
- `external_id` único por empresa;
- data (`day_iso`);
- título;
- quantidade de vagas bloqueadas (`blocked_slots`);
- `all_day`;
- observação;
- usuário criador;
- exclusão lógica.

### Endpoints autenticados
- `GET /api/booking/personal-tasks?include_deleted=true`
- `POST /api/booking/personal-tasks`

O POST funciona como UPSERT por `company_id + external_id`.

## 2. Efeito na Agenda Online
A tarefa não vira agendamento falso.

Ela atua somente sobre capacidade/disponibilidade:
- `blocked_slots=N` reserva N vagas do dia;
- `all_day=true` torna a data indisponível;
- exclusão lógica libera novamente a capacidade.

O calendário público considera clientes + vagas bloqueadas ao calcular lotação.
A disponibilidade pública reduz os horários/vagas ofertados.

Por privacidade, título e observação da tarefa nunca são enviados à página pública.

## 3. Horários Personalizados
Novo campo de configuração:
`agendamento_online_horarios_personalizados`

`agendamento_online_modo` passa a aceitar:
- `flexivel`;
- `fixo`;
- `personalizado`.

Quando o modo é `personalizado`, a página pública usa somente os horários informados pelo DS Go, preservando minutos arbitrários como `09:10`, `11:25`, `15:40`.

O domingo especial continua com prioridade aos domingos e usa seus campos próprios da V1.0.1.16.

## 4. Autoridade
`agendamento_online_horarios_personalizados` entra em `DS_GO_AUTHORITY_SETTINGS`.

Assim, o DSYSTEM STUDIO não pode sobrescrever os horários personalizados definidos pelo DS Go.

As demais regras de autoridade anteriores permanecem intactas.

## 5. Compatibilidade preservada
Preserva integralmente:
- domingo especial V1.0.1.16;
- meses da Agenda Online;
- link temporário individual de uso único;
- logo/identidade da empresa;
- tela Agenda Fechada;
- cliente novo/STR;
- ONLINE-UUID;
- UPSERT;
- isolamento multiempresa;
- login e sincronização Studio/Go.

## Integração
Usar com:
- DS Go `V1.0.0.36`;
- DSYSTEM STUDIO `V7.9.5.110`.

No Render:
`APP_VERSION=1.0.1.17`

## Validação executada
- `python -m compileall` em `app/` e `scripts/`: OK;
- teste SQLite em memória do modo Personalizado: OK;
- 3 horários personalizados retornados sem tarefa: OK;
- tarefa bloqueando 2 vagas deixou apenas 1 horário disponível: OK;
- tarefa `all_day` removeu toda a disponibilidade e marcou dia lotado: OK.

## Teste em produção recomendado
1. Subir a V1.0.1.17 no Render.
2. Definir `APP_VERSION=1.0.1.17`.
3. Publicar modo Personalizado pelo DS Go V36.
4. Criar tarefa parcial e consultar a mesma data na página pública.
5. Criar tarefa de dia inteiro e confirmar indisponibilidade.
6. Excluir a tarefa e confirmar retorno da capacidade.

## Próxima versão
`V1.0.1.18`
