# DSYSTEM SERVER CORE V1.0.1.2 — Modo Servidor Local em Rede

## Objetivo

Preparar o DSYSTEM SERVER CORE para rodar em um desktop/servidor local, sem depender de Cloudflared ou site externo, permitindo que o DSYSTEM STUDIO e o DS STUDIO GO acessem a API pelo IP da máquina na rede local.

## Arquitetura correta

```txt
Desktop servidor
    DSYSTEM SERVER CORE API
    http://IP-DA-MAQUINA:8000

DSYSTEM STUDIO Desktop
    aponta para http://IP-DA-MAQUINA:8000

DS STUDIO GO
    aponta para http://IP-DA-MAQUINA:8000
```

## Quando usar localhost

Use `http://localhost:8000` apenas quando o sistema cliente estiver aberto no mesmo computador onde a API está rodando.

No celular, tablet ou outro computador, use sempre o IP da máquina servidora:

```txt
http://192.168.x.x:8000
```

## Arquivos novos

### INICIAR_SERVIDOR_REDE.bat

Inicia a API em modo rede usando:

```txt
host: 0.0.0.0
porta: 8000
```

Mostra no terminal os endereços locais e os IPs para configurar no GO/STUDIO.

### LIBERAR_FIREWALL_PORTA_8000.bat

Libera a porta 8000 no Firewall do Windows.

Execute como Administrador.

### MOSTRAR_IP_SERVIDOR.bat

Mostra os IPs IPv4 disponíveis da máquina para usar no DS STUDIO GO ou no DSYSTEM STUDIO.

## Nova rota

```txt
GET /api/core/network-info
```

Retorna:

- versão da API;
- modo atual;
- URL local;
- URLs de rede detectadas;
- dica de configuração para o GO;
- company_slug padrão.

## Passo a passo para teste

1. No computador servidor, extraia o ZIP.
2. Execute `LIBERAR_FIREWALL_PORTA_8000.bat` como Administrador.
3. Execute `INICIAR_SERVIDOR_REDE.bat`.
4. Veja o IP mostrado, por exemplo:

```txt
http://192.168.110.236:8000
```

5. No navegador de outro dispositivo, teste:

```txt
http://192.168.110.236:8000/docs
```

6. No DS STUDIO GO, configure:

```txt
URL da API: http://192.168.110.236:8000
Company Slug: dsystem-master
```

7. No DSYSTEM STUDIO, configure a mesma URL da API.

## Base anterior

Base evoluída a partir de:

```txt
DSYSTEM_SERVER_CORE_V1.0.1.1_COMPATIBILIDADE_GO_COMPLETA
```

## Observação

Cloudflared pode ser usado como modo externo opcional, mas não é dependência principal da arquitetura local. O padrão oficial para servidor local é usar o IP da máquina servidora na rede.
