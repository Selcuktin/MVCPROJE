@echo off
color 0A
title Uzaktan Egitim Sistemi

echo ========================================
echo   UZAKTAN EGITIM SISTEMI
echo   Windows Yerel Kurulum
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo Python 3.8+ kurmaniz gerekiyor.
    pause
    exit /b 1
)
echo ✓ Python kurulu

echo.
echo [2/4] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment bulunamadi, olusturuluyor...
    python -m venv venv
    echo ✓ Virtual environment olusturuldu
) else (
    echo ✓ Virtual environment mevcut
)

echo.
echo [3/4] Activating environment...
call venv\Scripts\activate.bat

echo.
echo [4/4] Installing dependencies (ilk calisma)...
if not exist "venv\Lib\site-packages\django" (
    echo Django kuruluyor, lutfen bekleyin...
    pip install -q -r requirements.txt
    echo ✓ Paketler kuruldu
) else (
    echo ✓ Paketler zaten kurulu
)

echo.
echo ========================================
echo   MIGRATIONS KONTROL
echo ========================================
python manage.py migrate --no-input

echo.
echo ========================================
echo   SERVER BASLATILIYOR...
echo ========================================
echo.
echo ✓ Sistem hazir!
echo.
echo ERISIM BILGILERI:
echo -----------------------------------------
echo   Ana Sayfa:   http://localhost:8000
echo   Admin:       http://localhost:8000/admin
echo   API Docs:    http://localhost:8000/api/docs
echo -----------------------------------------
echo.
echo ILKONCE: python manage.py createsuperuser
echo ile admin kullanicisi olusturun!
echo.
echo Server'i durdurmak icin CTRL+C basin
echo.

python manage.py runserver

pause
