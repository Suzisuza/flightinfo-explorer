@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Preparing the Python environment...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        where python >nul 2>nul
        if errorlevel 1 goto :python_error
        python -m venv .venv
    )
    if errorlevel 1 goto :python_error
)

echo Installing required packages...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :install_error

for /f %%P in ('powershell -NoProfile -Command "$candidate = 5000; while ($true) { $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $candidate); try { $listener.Start(); $listener.Stop(); break } catch { $candidate++ } }; Write-Output $candidate"') do set "APP_PORT=%%P"
if not defined APP_PORT goto :port_error

echo Starting FlightInfo Explorer...
echo Opening the app on http://127.0.0.1:%APP_PORT%/
start "FlightInfo Explorer server" /D "%~dp0" "%~dp0.venv\Scripts\python.exe" -m flask --app flightinfo_app run --host 127.0.0.1 --port %APP_PORT%
timeout /t 3 /nobreak >nul
set "EDGE_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE_EXE%" set "EDGE_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if exist "%EDGE_EXE%" (
    start "" "%EDGE_EXE%" http://127.0.0.1:%APP_PORT%/
) else (
    start "" microsoft-edge:http://127.0.0.1:%APP_PORT%/
)
exit /b 0

:python_error
echo Python 3 could not be found. Install Python 3, then run this file again.
pause
exit /b 1

:install_error
echo Package installation failed. Check the internet connection and try again.
pause
exit /b 1

:port_error
echo A free local port could not be found. Close another local server and try again.
pause
exit /b 1
