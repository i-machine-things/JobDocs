@echo off
REM Quick version bump script for JobDocs (Windows)

setlocal

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Function to show usage
if "%1"=="" goto show
if "%1"=="-h" goto usage
if "%1"=="--help" goto usage
if "%1"=="help" goto usage

REM Check if python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: python is required but not found
    exit /b 1
)

REM Handle commands
if "%1"=="show" goto show
if "%1"=="info" goto show
if "%1"=="current" goto show
if "%1"=="patch" goto patch
if "%1"=="minor" goto minor
if "%1"=="major" goto major
if "%1"=="set" goto set_version

echo Error: Unknown command '%1'
echo.
goto usage

:show
python "%SCRIPT_DIR%update_version.py"
goto end

:patch
python "%SCRIPT_DIR%update_version.py" patch
goto end

:minor
python "%SCRIPT_DIR%update_version.py" minor
goto end

:major
python "%SCRIPT_DIR%update_version.py" major
goto end

:set_version
if "%2"=="" (
    echo Error: 'set' command requires a version argument
    echo Example: bump_version.bat set 1.0.0
    exit /b 1
)
python "%SCRIPT_DIR%update_version.py" set %2
goto end

:usage
echo JobDocs Version Bump Utility
echo.
echo Usage:
echo   bump_version.bat [command] [version]
echo.
echo Commands:
echo   show               Show current version information (default^)
echo   patch              Bump patch version (0.2.0 -^> 0.2.1^)
echo   minor              Bump minor version (0.2.0 -^> 0.3.0^)
echo   major              Bump major version (0.2.0 -^> 1.0.0^)
echo   set ^<version^>      Set specific version (e.g., 1.0.0 or 1.0.0-beta^)
echo.
echo Examples:
echo   bump_version.bat                # Show current version
echo   bump_version.bat patch          # Bump patch number
echo   bump_version.bat set 1.0.0      # Set to version 1.0.0
echo   bump_version.bat set 1.0.0-rc1  # Set to 1.0.0-rc1
goto end

:end
endlocal
