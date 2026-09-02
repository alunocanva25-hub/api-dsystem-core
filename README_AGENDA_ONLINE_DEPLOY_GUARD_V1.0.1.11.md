# DSYSTEM SERVER CORE V1.0.1.11 — AGENDA ONLINE DEPLOY GUARD

## Motivo desta revisão

A V1.0.1.10 recebida foi validada localmente e já registra corretamente o router de Agenda Online.

Rotas confirmadas no pacote V1.0.1.10:

- `GET /api/booking/config`
- `PUT /api/booking/config`
- `POST /api/studio/public-booking/config`
- `GET /api/public/booking/{slug}/config`
- `GET /api/public/booking/{slug}/clients/search`
- `GET /api/public/booking/{slug}/availability`
- `POST /api/public/booking/{slug}/appointments`
- `GET/POST /agendamento-publico/{slug}`
- `GET /agendamento-publico`

O `app/main.py` da V1.0.1.10 também já contém `app.include_router(public_booking.router)`.

Portanto, o retorno genérico `{"detail":"Not Found"}` observado no Render não é produzido pela V1.0.1.10 enviada para análise. A causa mais provável é que o serviço Render esteja executando outra revisão do repositório, outra branch/root directory, ou um commit em que o módulo ainda não chegou.

## O que muda na V1.0.1.11

Nenhuma lógica funcional da Agenda Online foi reescrita.

Alterações cirúrgicas:

1. `app/core/config.py`
   - versão padrão alterada de `1.0.1.10` para `1.0.1.11`.

2. `.env.example`
   - `APP_VERSION=1.0.1.11`.

3. `docker-compose.yml` e `scripts/init_db.py`
   - identificação de versão atualizada para `1.0.1.11` nos ambientes/logs locais.

4. `app/main.py`
   - mantém `app.include_router(public_booking.router)`;
   - adiciona marcador fixo de build: `DSYSTEM_SERVER_CORE_V1.0.1.11_AGENDA_ONLINE_DEPLOY_GUARD`;
   - adiciona `GET /api/core/deploy-info`;
   - registra no log de boot do Render se `/agendamento-publico/{slug}` foi realmente carregada.

## Como validar depois do deploy

Abrir:

`https://agenda.dsystemstudio.com.br/api/core/deploy-info`

Resultado esperado deve conter:

```json
{
  "ok": true,
  "build_id": "DSYSTEM_SERVER_CORE_V1.0.1.11_AGENDA_ONLINE_DEPLOY_GUARD",
  "public_booking_router_loaded": true,
  "expected_public_booking_route": "/agendamento-publico/{slug}"
}
```

Depois abrir:

`https://agenda.dsystemstudio.com.br/agendamento-publico/dsystem-master`

Se o router estiver carregado, o retorno não poderá mais ser o `{"detail":"Not Found"}` genérico da FastAPI.

Se aparecer `Agenda Online indisponível para esta empresa`, a Etapa de deploy da rota estará resolvida e o próximo ponto será somente habilitar/publicar a configuração da Agenda Online para `dsystem-master`.

## Render — conferir obrigatoriamente

- repositório conectado;
- branch usada pelo serviço;
- Root Directory;
- commit do último deploy;
- se `app/routes/public_booking.py` existe nesse commit;
- se `app/main.py` desse commit contém `app.include_router(public_booking.router)`;
- se o log de boot mostra `[DSYSTEM DEPLOY] DSYSTEM_SERVER_CORE_V1.0.1.11_AGENDA_ONLINE_DEPLOY_GUARD`.

Não alterar Cloudflare, CNAME ou certificado nesta etapa.

`PUBLIC_BOOKING_BASE_URL` pode continuar vazio; ela não controla o registro da rota.
