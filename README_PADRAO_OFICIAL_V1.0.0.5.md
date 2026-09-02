# DSYSTEM SERVER CORE V1.0.0.5 - API PADRÃO OFICIAL

Esta versão formaliza os nomes e códigos oficiais dos módulos iniciais do ecossistema DSYSTEM.

## Login local padrão

```json
{
  "username": "master",
  "password": "master123",
  "company_slug": "dsystem-master"
}
```

Após receber o `access_token`, use no Swagger em **Authorize**:

```txt
Bearer SEU_TOKEN_AQUI
```

## Rotas novas

```txt
GET /api/core/official-standards
GET /api/core/integration-map
```

## Module codes oficiais

```txt
core
hub
studio
studio_go
dsystem_ar
dsystem_ar_painel
pulselab
vision
bike
pousada
vm
inventario
winthor_tools
```

## Regra oficial de sincronização

Para evitar duplicidade, cada registro sincronizado deve respeitar:

```txt
company_id + module_code + external_id
```

Exclusão deve ser lógica:

```txt
is_deleted = true
deleted_at = data/hora
```

Regra crítica: se a API retornar vazia, o app cliente não deve apagar os dados locais automaticamente.

## Ordem de integração recomendada

```txt
1. Finalizar API CORE
2. Adaptar DS STUDIO GO
3. Adaptar DSYSTEM AR
4. Adaptar DSYSTEM-AR-PAINEL
5. Adaptar DSYSTEM STUDIO Desktop
6. Conectar DSYSTEM HUB
```
