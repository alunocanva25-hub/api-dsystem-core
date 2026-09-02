# DSYSTEM SERVER CORE — CONTEXTO OFICIAL V1.0.1.10

Base anterior: `DSYSTEM_SERVER_CORE_V1.0.1.9_CONCILIAR_CODIGOS_STUDIO`.
Base atual: `DSYSTEM_SERVER_CORE_V1.0.1.10_AGENDAMENTO_ONLINE_CORE`.

## Função principal desta versão

A CORE passa a hospedar e processar a Agenda Online multiempresa. O agendamento público nasce diretamente na CORE e é distribuído para DS Go e DSYSTEM STUDIO.

## Contrato de identidade

- empresa pública: `company_slug` -> `company_id`;
- cliente do Studio: `STRxxxx`;
- agendamento online: `ONLINE-UUID`;
- chave anti-duplicação: `company_id + module_code + external_id`;
- origem: `online_booking`.

## Segurança/privacidade pública

- nenhum endpoint público aceita `company_id` arbitrário; a empresa é resolvida pelo slug;
- busca de cliente é limitada à empresa;
- WhatsApp retornado na pesquisa pública é mascarado;
- endpoints administrativos/configuração exigem sessão CORE.

## Integração coordenada

Usar com:
- `DSYSTEM_STUDIO_UPDATE_V7.9.5.106_AGENDAMENTO_ONLINE_CORE`;
- `DS_GO_V1.0.0.25_FLUTTER_COMPLETO`.

## Cloudflare

O domínio `agenda.dsystemstudio.com.br` estava apontando para o notebook via Cloudflared. Código sozinho não altera esse túnel/DNS. Para a nova arquitetura funcionar com notebook desligado, apontar o domínio para a CORE (diretamente ou por proxy/Worker). Até isso ser feito, o link direto da CORE funciona normalmente.

## Validação local realizada

- login CORE;
- publicação da configuração;
- isolamento entre duas empresas com o mesmo `STR0001`;
- disponibilidade;
- criação de `ONLINE-UUID`;
- consulta pelo endpoint usado pelo DS Go;
- pull do Studio com `sources=go_mobile,online_booking`;
- reenvio do mesmo `external_id` atualiza a linha existente e não duplica;
- origem `online_booking` preservada mesmo após update vindo do desktop.

Próxima versão CORE: `V1.0.1.11`.
