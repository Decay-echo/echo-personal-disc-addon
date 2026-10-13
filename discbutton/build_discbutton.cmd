@echo off
rem Builds DiscButton.dll (EchoLoader plugin) and discbutton_test.exe into discbutton\build.
setlocal
if not defined VCVARS (
  for /f "usebackq delims=" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VCVARS=%%i\VC\Auxiliary\Build\vcvars64.bat"
)
if not exist "%VCVARS%" (echo ERROR: Visual Studio C++ tools not found & exit /b 1)
call "%VCVARS%" >nul 2>nul
cd /d "%~dp0"
if not exist build mkdir build
set CFLAGS=/nologo /O2 /MT /W4 /EHsc /std:c++17 /DUNICODE /D_UNICODE /wd4100
cl /nologo /O2 /MT /c /TC minhook\src\buffer.c minhook\src\hook.c minhook\src\trampoline.c minhook\src\hde\hde64.c /Fo:build\
if errorlevel 1 exit /b 1
cl %CFLAGS% /LD discbutton.cpp build\buffer.obj build\hook.obj build\trampoline.obj build\hde64.obj /Fo:build\ /Fe:build\DiscButton.dll /link /IMPLIB:build\DiscButton.lib
if errorlevel 1 exit /b 1
cl %CFLAGS% discbutton_test.cpp build\buffer.obj build\hook.obj build\trampoline.obj build\hde64.obj /Fo:build\ /Fe:build\discbutton_test.exe
exit /b %errorlevel%
