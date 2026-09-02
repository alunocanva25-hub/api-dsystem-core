@echo off
chcp 65001 >nul
setlocal

echo ==========================================================
echo  LIBERAR FIREWALL - DSYSTEM SERVER CORE PORTA 8000
echo ==========================================================
echo.
echo Este script precisa ser executado como ADMINISTRADOR.
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: execute este arquivo como Administrador.
    echo Clique com o botao direito e escolha "Executar como administrador".
    pause
    exit /b 1
)

netsh advfirewall firewall add rule name="DSYSTEM SERVER CORE API 8000" dir=in action=allow protocol=TCP localport=8000 profile=any

echo.
echo Regra criada/atualizada para liberar acesso TCP na porta 8000.
echo Agora rode INICIAR_SERVIDOR_REDE.bat e configure o GO com http://IP-DA-MAQUINA:8000
echo.
pause
