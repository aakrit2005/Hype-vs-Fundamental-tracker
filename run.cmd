@echo off
setlocal enabledelayedexpansion
rem Single launcher for Windows: data pipeline + backend + frontend.
rem Usage:
rem   run.cmd            pipeline (skipped if already ran today) then both servers
rem   run.cmd pipeline   force the data cycle only
rem   run.cmd servers    skip the data cycle, just serve

cd /d "%~dp0"

rem Windows gets its own virtualenv so a shared drive never fights with Linux.
set PY=backend\.venv-win\Scripts\python.exe
set STAMP=%TEMP%\hype-tracker-pipeline.stamp

rem ---------- preflight checks ----------
where python >nul 2>&1 || ( echo ERROR: python not found on PATH. Install Python 3.10+ first. & exit /b 1 )

if not exist "%PY%" (
  echo ==^> Creating Windows virtualenv and installing dependencies (first run only, takes a few minutes)
  python -m venv backend\.venv-win || exit /b 1
  "%PY%" -m pip install --upgrade pip || exit /b 1
  "%PY%" -m pip install -r backend\requirements-dev.txt || exit /b 1
)

if not exist backend\.env (
  echo ERROR: backend\.env is missing. It must contain SERPAPI_KEY and JWT_SECRET.
  exit /b 1
)

where npm >nul 2>&1 || ( echo ERROR: npm not found. Install Node 20+ first. & exit /b 1 )

rem node_modules is platform-specific: reinstall if it was built by another OS.
if not exist frontend\node_modules\@esbuild\win32-x64 (
  echo ==^> Installing frontend dependencies for Windows
  if exist frontend\node_modules rmdir /s /q frontend\node_modules
  pushd frontend
  if exist package-lock.json (call npm ci) else (call npm install)
  popd
)

rem ---------- today's date for the once-per-day stamp ----------
for /f %%a in ('powershell -noprofile -command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%a

rem ---------- modes ----------
if /i "%~1"=="pipeline" goto pipeline
if /i "%~1"=="servers" goto servers
if /i "%~1"=="" goto all
echo Usage: run.cmd [all ^| pipeline ^| servers]
exit /b 1

:all
set STAMPED=
if exist "%STAMP%" set /p STAMPED=<"%STAMP%"
if "!STAMPED!"=="%TODAY%" (
  echo ==^> Pipeline already ran today, skipping. (Use "run.cmd pipeline" to force it.)
) else (
  call :pipeline_steps || exit /b 1
)
goto servers

:pipeline
call :pipeline_steps
exit /b %errorlevel%

:pipeline_steps
echo ==^> [1/3] Refreshing price history
"%PY%" scripts\backfill_prices.py || exit /b 1
echo ==^> [2/3] Ingesting news, scoring, evaluating alerts
"%PY%" scripts\daily_update.py || exit /b 1
echo ==^> [3/3] Measuring the signal (backtest)
"%PY%" scripts\run_backtest.py || exit /b 1
> "%STAMP%" echo %TODAY%
echo ==^> Pipeline complete.
exit /b 0

:servers
echo ==^> Starting backend  -^>  http://127.0.0.1:8000   (API docs: /docs)
start "Hype Backend" cmd /k ""%PY%" -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000"
echo ==^> Starting frontend -^>  http://localhost:5173
start "Hype Frontend" cmd /k "npm --prefix frontend run dev"
echo.
echo Both services are running in their own windows.
echo Close those windows, or run stop.cmd, to shut everything down.
exit /b 0