<#
.SYNOPSIS
    SociSenti Platform Management Script for Windows PowerShell
.DESCRIPTION
    Provides equivalent targets to the Makefile for native Windows users:
    ./run.ps1 up
    ./run.ps1 down
    ./run.ps1 seed
    ./run.ps1 test
    ./run.ps1 demo
#>

param (
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "seed", "test", "lint", "demo", "help")]
    [string]$Target = "help"
)

$PythonPath = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) {
    $PythonPath = "python.exe"
}

switch ($Target) {
    "up" {
        Write-Host "Starting Supabase local stack and Docker compose..." -ForegroundColor Cyan
        npx supabase start
        docker compose up -d
    }
    "down" {
        Write-Host "Stopping Docker compose and Supabase stack..." -ForegroundColor Yellow
        docker compose down
        npx supabase stop
    }
    "seed" {
        Write-Host "Generating synthetic dataset and running migrations..." -ForegroundColor Cyan
        & $PythonPath data/generate_sample.py
        npx supabase db reset --linked=false
    }
    "test" {
        Write-Host "Running test suite..." -ForegroundColor Cyan
        & $PythonPath -m pytest -v tests/
    }
    "lint" {
        Write-Host "Running ruff check..." -ForegroundColor Cyan
        & $PythonPath -m ruff check .
    }
    "demo" {
        Write-Host "Running end-to-end replay demo..." -ForegroundColor Cyan
        & $PythonPath -m services.demo
    }
    "help" {
        Write-Host "Usage: .\run.ps1 [up | down | seed | test | lint | demo]" -ForegroundColor Green
    }
}
