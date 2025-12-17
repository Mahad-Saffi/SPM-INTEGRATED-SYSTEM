@echo off
echo 🚀 Starting Project Management Orchestrator...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
pip install -q -r requirements.txt

REM Create .env if it doesn't exist
if not exist ".env" (
    echo ⚙️  Creating .env file...
    copy .env.example .env 2>nul || (
        echo DATABASE_URL=postgresql+asyncpg://admin:secure_password@localhost:5432/project_management > .env
    )
)

REM Run the application
echo.
echo ✅ Starting orchestrator on http://localhost:9000
echo 📖 API Documentation: http://localhost:9000/docs
echo.
python main.py

pause
