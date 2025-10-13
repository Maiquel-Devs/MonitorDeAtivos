@echo off
ECHO Iniciando o Projeto Falcao...

REM Define o caminho para a pasta do seu projeto. Confirme se esta linha está correta!
SET "PROJECT_PATH=C:\Users\junio\OneDrive\Documentos\Estudos\MonitorDeAtivos\falcao_investidor"

ECHO --- Ligando o Worker do Celery (Cozinheiro) ---
REM O comando /k mantém a janela do terminal aberta para vermos os logs
START "Celery Worker" cmd /k "cd /d %PROJECT_PATH% && venv\Scripts\activate && celery -A projeto_falcao worker -l info -P eventlet"

ECHO --- Ligando o Servidor Django (Garcom) ---
START "Django Server" cmd /k "cd /d %PROJECT_PATH% && venv\Scripts\activate && python manage.py runserver"

ECHO Aguardando os servidores iniciarem...
REM Dá um tempo para os servidores subirem antes de abrir o navegador
timeout /t 5 >nul

ECHO --- Abrindo o Dashboard no Navegador ---
start http://127.0.0.1:8000/

ECHO.
ECHO Processo de inicializacao completo!