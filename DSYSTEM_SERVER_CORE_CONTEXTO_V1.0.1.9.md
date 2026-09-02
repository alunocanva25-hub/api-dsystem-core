# DSYSTEM SERVER CORE — CONTEXTO OFICIAL V1.0.1.9

## BASE ATUAL
`DSYSTEM_SERVER_CORE_V1.0.1.9_CONCILIAR_CODIGOS_STUDIO`

Versão anterior: `DSYSTEM_SERVER_CORE_V1.0.1.8_PRESERVAR_CODIGOS_STUDIO`

## OBJETIVO
A V1.0.1.8 passou a preservar códigos `STRxxxx`. A V1.0.1.9 completa a correção conciliando clientes antigos que já estavam persistidos como `CLI-X`, `CLI_*`, `API_CLIENT_*` ou `GO_CLIENT_*`, evitando que o próximo sync do Studio crie uma segunda pessoa com STR.

## REGRA DE CONCILIAÇÃO
A migração automática só ocorre quando o cliente novo possui STR válida (`STR` + 4 dígitos) e existe evidência forte de que o registro legado é a mesma pessoa:
- external_id legado explícito no payload;
- STR já preservada no raw_payload do registro legado;
- documento idêntico;
- nome + e-mail idênticos;
- nome + telefone idênticos.

Se houver empate entre candidatos, a CORE não mescla automaticamente.

## COMPORTAMENTO
- Sem STR existente: o próprio registro CLI-X é migrado para STRxxxx.
- STR e CLI-X já duplicados: a STR permanece ativa e o legado é marcado como mesclado/excluído.
- Agenda e Financeiro com `customer_external_id=CLI-X` são repontados para STRxxxx.
- O ID antigo fica em `legacy_external_id` e `legacy_external_ids` para auditoria.

## ROTA ADMINISTRATIVA
`POST /api/admin/reconcile-client-codes`

Exige MASTER/ADMIN. Pode receber `company_id` como query parameter; sem ele, usa a empresa do usuário autenticado. Serve para conciliar registros já existentes na base.

## TESTES EXECUTADOS NESTE PATCH
1. Cliente Maria: `CLI-3` + payload Studio `STR0000` -> um único registro ativo `STR0000`.
2. Appointment e Transaction vinculados a `CLI-3` -> repontados para `STR0000`.
3. Duplicata Joao: `CLI-4` e `STR0001` existentes -> apenas `STR0001` permanece ativa.
4. `app.main` importa normalmente e expõe a rota administrativa.
5. `compileall` Python sem erros.

## DEPLOY
Definir `APP_VERSION=1.0.1.9`. Não há mudança obrigatória de schema/tabela.

## COMPATIBILIDADE DS GO
Par recomendado: `DS Go V1.0.0.16`.
