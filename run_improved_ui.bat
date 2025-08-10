@echo off
echo Starting Improved P2P Chat Textual UI...
echo.

:: Try to use the full Python path
set PYTHON_PATH=C:\Users\Zurax\AppData\Local\Programs\Python\Python313\python.exe

:: Check if the specified Python exists
if exist "%PYTHON_PATH%" (
    echo Using Python: %PYTHON_PATH%
    "%PYTHON_PATH%" improved_textual_ui.py
) else (
    echo Python path not found: %PYTHON_PATH%
    echo Trying system Python...
    
    :: Fall back to the system Python
    python improved_textual_ui.py
)

:: Pause so the user can see any error messages
pause
