@echo off
setlocal

REM Task name
set TASK_NAME=NewsAnalyzerPythonServer

REM Get the current directory (where this .bat file is located)
set SERVER_DIR=%~dp0
set SERVER_SCRIPT=%SERVER_DIR%Server.py

REM Delete the existing scheduled task if it exists
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Task "%TASK_NAME%" already exists. Deleting it...
    schtasks /Delete /TN "%TASK_NAME%" /F
)

REM Create a new task that references the same terminal (cmd window)
echo Creating Task "%TASK_NAME%" linked to this terminal...
schtasks /Create /F /RL HIGHEST /SC ONCE /ST 00:00 /TN "%TASK_NAME%" /TR "\"cmd /c start /b python \"%SERVER_SCRIPT%\"\""

if %ERRORLEVEL%==0 (
    echo Task "%TASK_NAME%" created successfully.
    echo The server will now be managed to persist in this terminal window.
) else (
    echo Failed to create Task "%TASK_NAME%". Please check your paths and permissions.
    goto end
)

REM Start the Python server directly in this terminal window
echo Starting the server in this terminal...
python "%SERVER_SCRIPT%"

:end
pause
