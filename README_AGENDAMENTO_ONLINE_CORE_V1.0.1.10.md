# DSYSTEM SERVER CORE V1.0.1.10 — AGENDAMENTO ONLINE CORE

## Objetivo

Transformar a CORE no ponto central da Agenda Online, retirando a dependência do notebook/DSYSTEM STUDIO ligado para receber novos agendamentos.

## Fluxo oficial

```text
Cliente
  -> /agendamento-publico/{company_slug}
  -> CORE resolve company_slug -> company_id
  -> cria ONLINE-UUID uma única vez
  -> DS Go recebe pela API
  -> DSYSTEM STUDIO recebe pelo pull
```

## Multiempresa

Todos os dados públicos são resolvidos primeiro pelo `Company.slug`. Depois disso, consultas e gravações usam obrigatoriamente o `company_id` da empresa resolvida. Clientes, serviços, profissionais, disponibilidade e agendamentos de empresas diferentes não são misturados.

## Novas rotas

Autenticadas:
- `GET /api/booking/config`
- `PUT /api/booking/config`
- `POST /api/studio/public-booking/config`

Públicas:
- `GET /api/public/booking/{slug}/config`
- `GET /api/public/booking/{slug}/clients/search?q=...`
- `GET /api/public/booking/{slug}/availability`
- `POST /api/public/booking/{slug}/appointments`
- `GET/POST /agendamento-publico/{slug}`
- `GET /agendamento-publico`

## Já sou cliente

A página preserva o fluxo existente do Studio e permite localizar cadastro por STR/código, WhatsApp ou nome. O retorno público mascara o WhatsApp e a CORE só pesquisa dentro da empresa do slug.

## Clientes novos

Cliente novo criado pela página recebe `STR0000..STR9999` dentro da própria empresa, com `sync_source=online_booking`.

## Agendamento online

Cada agendamento público recebe um `external_id` único no formato:

`ONLINE-<UUID>`

A chave única da CORE continua sendo `(company_id, module_code, external_id)`, portanto o mesmo agendamento pode ser baixado pelo DS Go e pelo Studio sem criar uma segunda linha na CORE.

## Pull do Studio

As rotas `/api/studio/pull/*` agora aceitam o parâmetro opcional `sources`. O Studio V7.9.5.106 usa `go_mobile,online_booking` para clientes/agendamentos.

## Configuração da página

A tabela `public_booking_configs` mantém as preferências por empresa. Studio e DS Go podem atualizar conjuntos parciais de configuração sem apagar campos que pertencem ao outro cliente.

## Hospedagem

A página HTML/CSS agora faz parte da CORE. Para independência real do notebook, o domínio público deve apontar para o serviço da CORE, e não para o túnel Cloudflared local do notebook.

Variável opcional:

`PUBLIC_BOOKING_BASE_URL=https://agenda.dsystemstudio.com.br/agendamento-publico`

Enquanto o domínio ainda não estiver redirecionado para a CORE, use o endereço direto da CORE:

`<CORE_BASE_URL>/agendamento-publico/<company_slug>`

## Banco

O Dockerfile executa `python scripts/init_db.py` antes do Uvicorn para garantir a criação da nova tabela `public_booking_configs` em deploys existentes.
