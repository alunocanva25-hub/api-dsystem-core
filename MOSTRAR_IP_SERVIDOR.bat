@echo off
chcp 65001 >nul
setlocal

echo ==========================================================
echo  IPs DA MAQUINA - DSYSTEM SERVER CORE
echo ==========================================================
echo.
echo Use um destes enderecos no DS STUDIO GO ou DSYSTEM STUDIO:
echo.
for /f "tokens=*" %%A in ('powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Select-Object -ExpandProperty IPAddress"') do (
    echo http://%%A:8000
)
echo.
echo Documentacao Swagger:
for /f "tokens=*" %%A in ('powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Select-Object -ExpandProperty IPAddress"') do (
    echo http://%%A:8000/docs
)
echo.
pause
