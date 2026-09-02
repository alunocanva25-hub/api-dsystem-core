@echo off
setlocal
cd /d %~dp0

echo ===============================================
echo  DSYSTEM SERVER CORE V1.0.1.2 - MODO LOCAL
echo ===============================================
echo.

if not exist .venv (
    echo Criando ambiente virtual local...
    python -m venv .venv
)

call .venv\Scripts\activate

echo.
echo Atualizando ferramentas de instalacao...
python -m pip install --upgrade pip setuptools wheel

echo.
echo Instalando dependencias locais SQLite...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo FALHA AO INSTALAR DEPENDENCIAS.
    echo Dica: se estiver usando Python muito novo, tente Python 3.12 ou 3.13.
    pause
    exit /b 1
)

if not exist .env copy .env.example .env

echo.
echo Inicializando banco local...
python scripts\init_db.py
if errorlevel 1 (
    echo.
    echo FALHA AO INICIALIZAR BANCO.
    pause
    exit /b 1
)

echo.
echo Servidor iniciado em: http://localhost:8000/docs
echo Login inicial: master / master123
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
