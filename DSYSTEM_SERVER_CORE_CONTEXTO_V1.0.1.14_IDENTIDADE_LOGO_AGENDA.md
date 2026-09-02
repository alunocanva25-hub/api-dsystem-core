# DSYSTEM SERVER CORE V1.0.1.14 — IDENTIDADE/LOGO NA AGENDA ONLINE

Base: `V1.0.1.13_AGENDA_FECHADA`.

## Alteração
- CORE passa a aceitar `settings.logo_data_url` enviado pelo DSYSTEM STUDIO.
- Imagem aceita: PNG, JPEG, WEBP ou GIF em data URL base64, limitada a ~1,6 MB de arquivo.
- Página pública normal exibe a logo da empresa ao lado do nome quando disponível.
- Tela **Agenda fechada** substitui o ícone fixo pela logo da empresa quando disponível.
- Sem logo, o fallback visual anterior é mantido.
- `marca_texto`/`studio_nome` continuam definindo o nome mostrado (ex.: `STUDIO RY`).

## Preservado
- DS Go continua autoridade de `enabled`, modo e horários fixos.
- Página fechada da V1.0.1.13.
- Login, usuários, clientes, serviços, profissionais, disponibilidade, ONLINE-UUID e UPSERT.

## Deploy
No Render usar `APP_VERSION=1.0.1.14`.
Após deploy, executar sincronização no Studio V7.9.5.110 para enviar a logo.
