@echo off
setlocal
cd /d %~dp0

echo Esta rotina apaga o ambiente virtual local e o banco SQLite de teste.
echo Use quando uma instalacao anterior ficou incompleta.
echo.
set /p CONFIRMA=Deseja continuar? Digite SIM: 
if /I not "%CONFIRMA%"=="SIM" exit /b 0

if exist .venv rmdir /s /q .venv
if exist dsystem_core.db del /q dsystem_core.db

echo Ambiente resetado. Agora execute RUN_LOCAL.bat novamente.
pause
