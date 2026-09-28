@echo off
rem ---------------------------------------------------------------
rem  StyleFlow launcher (Windows)
rem  Keep this file ASCII-only: cmd.exe parses .bat using the ANSI
rem  code page, so non-ASCII text here would break the script.
rem  All Chinese messages are printed by start.py (UTF-8 aware).
rem ---------------------------------------------------------------
chcp 65001 >nul
cd /d "%~dp0"
title StyleFlow

where py >nul 2>nul
if not errorlevel 1 goto usepy

where python >nul 2>nul
if not errorlevel 1 goto usepython

echo.
echo [ERROR] Python not found.
echo         Please install Python 3.12+ : https://www.python.org/downloads/
echo         Tick "Add python.exe to PATH" while installing, then run this file again.
echo.
pause
exit /b 1

:usepy
py -3 "%~dp0start.py" %*
goto finished

:usepython
python "%~dp0start.py" %*
goto finished

:finished
set EXIT_CODE=%ERRORLEVEL%
if not "%EXIT_CODE%"=="0" (
  echo.
  echo [ERROR] Startup failed. Please screenshot the message above.
  pause
)
exit /b %EXIT_CODE%
