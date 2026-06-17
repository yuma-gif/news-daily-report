@echo off
setlocal EnableDelayedExpansion

for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"

pushd "%PROJECT_ROOT%" || (
    if not exist "%~dp0..\logs" mkdir "%~dp0..\logs"
    echo ==================================================>> "%~dp0..\logs\scheduler.log"
    echo Start time: %date% %time%>> "%~dp0..\logs\scheduler.log"
    echo Failed to switch to project root: %PROJECT_ROOT%>> "%~dp0..\logs\scheduler.log"
    echo End time: %date% %time%>> "%~dp0..\logs\scheduler.log"
    echo Exit code: 1>> "%~dp0..\logs\scheduler.log"
    exit /b 1
)

if not exist "logs" mkdir "logs"

echo ==================================================>> "logs\scheduler.log"
echo Start time: %date% %time%>> "logs\scheduler.log"
echo Project root: %CD%>> "logs\scheduler.log"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat" >> "logs\scheduler.log" 2>&1
)

echo Command: python -m src.main>> "logs\scheduler.log"
python -m src.main >> "logs\scheduler.log" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

echo End time: %date% %time%>> "logs\scheduler.log"
echo Exit code: !EXIT_CODE!>> "logs\scheduler.log"

popd
exit /b !EXIT_CODE!
