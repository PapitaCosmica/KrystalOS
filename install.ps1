<#
.SYNOPSIS
KrystalOS Smart Installer for Windows.
Automatiza la instalación de Python, Docker y Krystal CLI.
#>

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "    ✨ KRYSTAL OS - SMART INSTALLER ✨   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Este instalador verificará y preparará su entorno de desarrollo,"
Write-Host "instalando Python y Docker si no están presentes, y luego instalará"
Write-Host "KrystalOS globalmente."
Write-Host ""

# 1. Check/Install Python
Write-Host "[1/3] Verificando Python..." -ForegroundColor Yellow
$pythonCheck = Get-Command "python" -ErrorAction SilentlyContinue
if ($null -eq $pythonCheck) {
    Write-Host "❌ Python no está instalado. Iniciando instalación con Winget..." -ForegroundColor Red
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    Write-Host "✅ Python instalado correctamente. NOTA: Puede que necesite reiniciar su PC o terminal para que PATH se actualice." -ForegroundColor Green
} else {
    $pyVersion = python --version
    Write-Host "✅ Python detectado ($pyVersion)." -ForegroundColor Green
}

# 2. Check/Install Docker Desktop
Write-Host "`n[2/3] Verificando Docker Desktop..." -ForegroundColor Yellow
$dockerCheck = Get-Command "docker" -ErrorAction SilentlyContinue
if ($null -eq $dockerCheck) {
    Write-Host "❌ Docker no está instalado. Iniciando instalación con Winget..." -ForegroundColor Red
    winget install Docker.DockerDesktop --silent --accept-package-agreements --accept-source-agreements
    Write-Host "✅ Docker Desktop instalado." -ForegroundColor Green
    Write-Host "⚠️  ATENCIÓN: Debe abrir Docker Desktop manualmente al menos una vez y aceptar los términos." -ForegroundColor Red
} else {
    $dockerVersion = docker --version
    Write-Host "✅ Docker detectado ($dockerVersion)." -ForegroundColor Green
}

# 3. Install KrystalOS Globally
Write-Host "`n[3/3] Instalando KrystalOS CLI Globalmente..." -ForegroundColor Yellow
try {
    # Ensure pip is up to date
    python -m pip install --upgrade pip -q
    # Install the CLI from the current directory
    pip install -e .
    Write-Host "✅ Krystal CLI instalado en el entorno de Python." -ForegroundColor Green
} catch {
    Write-Host "❌ Ocurrió un error al instalar Krystal CLI con pip." -ForegroundColor Red
}

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "🎉 INSTALACIÓN COMPLETADA 🎉" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "`nSi el comando 'krystal' no funciona directamente, recuerde:"
Write-Host "1. Asegúrese de tener Python agregado a las variables de entorno (PATH)."
Write-Host "2. Asegúrese de que Docker Desktop esté corriendo en segundo plano."
Write-Host "`nPara iniciar un nuevo proyecto, escriba:" -ForegroundColor Yellow
Write-Host "krystal new NombreDeApp" -ForegroundColor White
Write-Host ""
Write-Host "Presione cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
