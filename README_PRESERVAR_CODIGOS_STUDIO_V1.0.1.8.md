# DSYSTEM SERVER CORE V1.0.1.8 — Preservar Códigos do Studio

## Objetivo

Corrige a compatibilidade de clientes vindos do DSYSTEM STUDIO para que a API CORE preserve o código/sigla original do Studio, como `STR0000`, em vez de substituir ou expor como `CLI-X`.

## Ajustes

- Clientes vindos do Studio agora priorizam `sigla`, `codigo`, `client_code`, `customer_code`, `codigo_cliente`, `cliente_codigo`, `cod_cliente` e `studio_code`.
- O `external_id` do cliente passa a preservar o código original do Studio quando disponível.
- A resposta para GO/Studio expõe aliases de compatibilidade: `external_id`, `codigo`, `sigla`, `client_code`, `customer_code` e `studio_code`.
- Agendamentos e financeiro passam a aceitar mais aliases para referência do cliente: `client_uid`, `codigo_cliente`, `cliente_codigo`, `client_code`, `customer_code` e `sigla_cliente`.
- Mantém a exclusão lógica GO → Studio da V1.0.1.5.
- Mantém diagnóstico/reset de senha da V1.0.1.7.

## Teste recomendado

1. Subir a API no Render.
2. Alterar `APP_VERSION=1.0.1.8`.
3. Sincronizar clientes pelo DSYSTEM STUDIO.
4. Conferir no Swagger se o cliente aparece como `STR0000` em `external_id`, `codigo`, `sigla` ou `client_code`.
5. Confirmar que não aparece mais `CLI-X` para cliente vindo do Studio.

## Observação

`CLI-X` ou `api_client_...` só deve ser usado para cliente criado diretamente pela API/GO sem código original do Studio.
