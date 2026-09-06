@echo off
setlocal EnableDelayedExpansion
title NexusRPG Launcher
cd /d "%~dp0"

echo ============================================
echo   NexusRPG - START
echo ============================================

:: ── 1. Python доступен? ──
set "PY=python"
%PY% --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден в PATH. Установите Python 3.11+.
    goto :fail
)

:: ── 2. venv есть? Нет — создать один раз ──
if exist "venv\Scripts\python.exe" (
    echo [OK] venv найден.
    set "PY=venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    echo [OK] .venv найден.
    set "PY=.venv\Scripts\python.exe"
) else (
    echo [SETUP] venv не найден, создаю venv...
    %PY% -m venv venv
    if errorlevel 1 ( echo [ОШИБКА] Не удалось создать venv. & goto :fail )
    set "PY=venv\Scripts\python.exe"
)

:: ── 3. Зависимости установлены? Проверка одним импортом, без переустановки ──
%PY% -c "import flask, requests" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Зависимости не обнаружены, ставлю requirements.txt — один раз...
    %PY% -m pip install --quiet -r requirements.txt
    if errorlevel 1 ( echo [ОШИБКА] Установка зависимостей не удалась. & goto :fail )
) else (
    echo [OK] Зависимости на месте.
)

:: ── 4. Порт сервера из src/config.py (не хардкодим) ──
for /f "tokens=*" %%P in ('%PY% -c "from src import config; print(config.PORT)" 2^>nul') do set "PORT=%%P"
if not defined PORT set "PORT=8080"
echo [OK] Порт сервера: %PORT%

:: ── 5. Сервер в фоновом окне; браузер — только когда порт отвечает ──
:: (раньше браузер открывался ДО старта сервера — race condition)
:: NEXUS_NO_BROWSER=1: браузер открывает сам .bat после опроса порта,
:: чтобы launcher.py не открыл второй вкладкой по слепой задержке.
:: NEXUS_NONINTERACTIVE=1: лаунчер не задаёт вопросов в свёрнутом окне
:: (иначе он может молча ждать ввода, а сервер никогда не стартует).
set "NEXUS_NO_BROWSER=1"
set "NEXUS_NONINTERACTIVE=1"
start "NexusRPG Server" /min "%PY%" launcher.py

echo [WAIT] Ожидаю готовности сервера (http://localhost:%PORT%) ...
set /a TRIES=0
:wait_loop
:: ping-делей ~2с (timeout /t не работает при перенаправленном stdin)
ping -n 3 127.0.0.1 >nul
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://localhost:%PORT%/' -UseBasicParsing -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto :server_ready
set /a TRIES+=1
if %TRIES% geq 45 goto :wait_timeout
echo     ... сервер ещё не готов — попытка %TRIES% из 45
goto :wait_loop

:server_ready
echo [OK] Сервер отвечает — открываю браузер.
start "" http://localhost:%PORT%
echo.
echo ==================================================
echo  Игра запущена:  http://localhost:%PORT%
echo  Сервер работает в свёрнутом окне "NexusRPG Server".
echo  Для остановки игры закройте ТО окно.
echo ==================================================
:: пауза ~10с, чтобы пользователь успел прочитать
ping -n 11 127.0.0.1 >nul
goto :eof

:wait_timeout
echo [ОШИБКА] Сервер не ответил за ~90 сек.
echo          Смотрите окно "NexusRPG Server": возможно, там вопрос лаунчера
echo          — установка Ollama или скачивание модели — либо текст ошибки.
goto :fail

:fail
echo.
echo Нажмите любую клавишу для закрытия...
pause >nul
exit /b 1
