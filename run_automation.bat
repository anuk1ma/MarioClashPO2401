@echo off
REM ========================================
REM Mario Clash - Automation Script (SIMPLE)
REM ========================================
REM 
REM ИНСТРУКЦИЯ:
REM 1. Измени путь ниже на ТВОЮ папку с игрой
REM 2. Сохрани файл
REM 3. Запусти
REM
REM ========================================

echo ========================================
echo Mario Clash - Database Automation
echo ========================================
echo [%date% %time%] Starting tasks...
echo.

REM ========================================
REM НАСТРОЙ ЭТИ ДВЕ СТРОКИ ПОД СЕБЯ:
REM ========================================

REM Путь к папке с игрой (ИЗМЕНИ НА СВОЙ!)
cd /d "C:\Users\anuk1ma\PycharmProjects\Platfromer"

REM Команда запуска Python (попробуй: python, py, или python3)
py automation_task.py

REM ========================================

if errorlevel 1 (
    echo.
    echo ERROR: Task failed!
    echo.
    echo Попробуй изменить команду Python на:
    echo   - py automation_task.py
    echo   - python3 automation_task.py
    echo   - "C:\Python311\python.exe" automation_task.py
    echo.
    pause
) else (
    echo.
    echo SUCCESS: Tasks completed!
    echo.
)

exit /b


