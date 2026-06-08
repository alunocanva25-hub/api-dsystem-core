# DSYSTEM SERVER CORE V1.0.1.0_ADMIN_EMPRESAS_USUARIOS

Base atual aprovada para evolução: API CORE com rotas administrativas para o futuro DSYSTEM HUB.

Consulte também: `README_ADMIN_V1.0.1.0.md` e `CHANGELOG_V1.0.1.0.txt`.

---

# DSYSTEM SERVER CORE V1.0.0.6_LOGIN_MODULOS

Backend central do ecossistema DSYSTEM.

Esta versão parte da V1.0.0.3 funcional e melhora o login para devolver o contexto completo do usuário: empresa, perfil, permissões e módulos liberados.

## Rodar localmente no Windows

Execute:

```bat
RUN_LOCAL.bat
```

Depois acesse:

```text
http://localhost:8000/
http://localhost:8000/docs
```

## Login inicial

```text
usuário: master
senha: master123
```

Payload em `/api/auth/login`:

```json
{
  "username": "master",
  "password": "master123"
}
```

Resposta agora inclui:

```text
access_token
token_type
expires_in_minutes
user
  ├── dados do usuário
  ├── company
  ├── modules
  └── permissions
```

## Novas rotas desta versão

```text
GET /api/auth/session
GET /api/auth/validate
GET /api/my/modules
```

Essas rotas foram criadas para o DS STUDIO GO, DSYSTEM STUDIO Desktop e demais ramificações saberem:

```text
quem está logado
qual empresa está usando
quais módulos estão liberados
qual perfil/permissão aplicar na tela
```

## Sync base mantido

Continuam disponíveis:

```text
POST /api/sync/clients
GET  /api/clients

POST /api/sync/appointments
GET  /api/appointments

POST /api/sync/transactions
GET  /api/transactions

POST /api/sync/studio
GET  /api/sync/logs
```

## Regra de não duplicidade

Os dados sincronizados continuam usando:

```text
company_id + module_code + external_id
```

## Observação

Se você já rodou a versão anterior e quiser banco limpo, execute:

```bat
RESETAR_AMBIENTE_LOCAL.bat
```

Como não houve alteração obrigatória em tabelas nesta versão, resetar não é obrigatório se a V1.0.0.3 já estava rodando bem.


## V1.0.0.6 - Padrão oficial

Consulte `README_PADRAO_OFICIAL_V1.0.0.6.md`.

Login local padrão:

```json
{
  "username": "master",
  "password": "master123",
  "company_slug": "dsystem-master"
}
```

Rotas novas:

```txt
GET /api/core/official-standards
GET /api/core/integration-map
```


## V1.0.0.6

Adicionado padrão DSYSTEM RETAIL com controle de segmento/plano pelo DSYSTEM SERVER CORE / HUB.


## V1.0.1.4 — Compatibilidade Financeira GO

Patch focado em `/api/transactions`, aliases financeiros e resumo de receitas/despesas/saldo para o DS STUDIO GO.
