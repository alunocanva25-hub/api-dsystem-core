# DSYSTEM SERVER CORE V1.0.1.6 - Correção Login Usuários Studio

## Problema corrigido

Após a V1.0.1.5, os usuários sincronizados pelo DSYSTEM STUDIO apareciam na API, mas o login retornava `Usuário ou senha inválidos`.

O diagnóstico mostrava:

```txt
company_found: true
user_found: true
user_active: true
password_valid: false
token_generated: false
```

## Correção

Esta versão mantém a exclusão lógica da V1.0.1.5 e corrige apenas a autenticação de usuários vindos do Studio.

A API agora aceita, na sincronização de usuários:

```txt
password
senha
pass
user_password
api_password
password_hash
senha_hash
hash_senha
pin
codigo_acesso
```

E valida temporariamente formatos legados de senha durante a migração:

```txt
pbkdf2_sha256 oficial
texto puro legado
sha256 hex legado
md5 hex legado
```

Quando o Studio envia senha em texto, a API salva novamente no padrão seguro PBKDF2.

## Teste recomendado

1. Subir a versão no Render.
2. Alterar `APP_VERSION=1.0.1.6`.
3. Sincronizar usuários novamente pelo DSYSTEM STUDIO.
4. Testar `/api/debug/login-check`.
5. Confirmar `password_valid=true` e `token_generated=true`.
6. Testar `/api/auth/login` com o usuário do Studio.
