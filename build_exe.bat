@echo off
echo ==========================================
echo   AI Agent - Build Executable
echo ==========================================
echo.
echo Press any key to start build...
pause >nul

echo.
echo [1/4] Installing Python dependencies...
echo Running: pip install -r requirements.txt
call pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)

echo.
echo [2/4] Building frontend...
cd /d "%~dp0frontend"
echo Running: npm install
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)
echo Running: npm run build
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm run build failed
    pause
    exit /b 1
)
cd /d "%~dp0"

echo.
echo [3/4] Cleaning old build...
if exist "dist\AI Agent.exe" del /f /q "dist\AI Agent.exe"
if exist "dist\AI Agent" rmdir /s /q "dist\AI Agent"
if exist "build" rmdir /s /q "build"

echo.
echo [4/4] Packing with PyInstaller (may take 3-5 min)...
echo Running: pyinstaller ai-agent.spec --clean
call pyinstaller ai-agent.spec --clean
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo Cleaning up build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist\AI Agent" rmdir /s /q "dist\AI Agent"
echo Done.

echo.
echo ==========================================
echo   BUILD COMPLETE!
echo   Output: dist\AI Agent.exe
echo ==========================================
pause