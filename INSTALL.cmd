@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 goto usepython
py -3 "%~dp0patch_personal_disc.py" %*
goto finished
:usepython
where python >nul 2>&1
if errorlevel 1 goto missing
python "%~dp0patch_personal_disc.py" %*
goto finished
:missing
echo Python 3 is required. Install Python 3 for Windows and try again.
:finished
echo.
pause
