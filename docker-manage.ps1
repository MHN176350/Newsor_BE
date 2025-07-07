# Docker Environment Management Script for Newsor (PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$Command
)

switch ($Command.ToLower()) {
    "docker-up" {
        Write-Host "🐳 Starting Newsor with Docker (PostgreSQL + Redis containers)..." -ForegroundColor Green
        if (Test-Path ".env.docker") {
            Copy-Item ".env.docker" ".env" -Force
        } else {
            Write-Host "Using current .env file" -ForegroundColor Yellow
        }
        docker-compose up --build
    }
    "docker-down" {
        Write-Host "🛑 Stopping Docker containers..." -ForegroundColor Red
        docker-compose down
    }
    "docker-clean" {
        Write-Host "🧹 Cleaning up Docker containers and volumes..." -ForegroundColor Yellow
        docker-compose down -v
        docker system prune -f
    }
    "local" {
        Write-Host "💻 Switching to local development environment..." -ForegroundColor Blue
        Copy-Item ".env.local" ".env" -Force
        Write-Host "Environment switched to local. Start your local PostgreSQL and Redis services." -ForegroundColor Green
    }
    "docker-env" {
        Write-Host "🐳 Switching to Docker environment..." -ForegroundColor Blue
        if (Test-Path ".env.docker") {
            Copy-Item ".env.docker" ".env" -Force
        } else {
            Write-Host "Docker .env file not found, using current .env" -ForegroundColor Yellow
        }
    }
    "migrate" {
        Write-Host "🔄 Running database migrations in Docker..." -ForegroundColor Cyan
        docker-compose exec web python manage.py migrate
    }
    "shell" {
        Write-Host "🐚 Opening Django shell in Docker container..." -ForegroundColor Cyan
        docker-compose exec web python manage.py shell
    }
    "logs" {
        Write-Host "📋 Showing Docker logs..." -ForegroundColor Cyan
        docker-compose logs -f
    }
    "status" {
        Write-Host "📊 Docker containers status:" -ForegroundColor Cyan
        docker-compose ps
    }
    default {
        Write-Host "🚀 Newsor Docker Management Script" -ForegroundColor Green
        Write-Host ""
        Write-Host "Usage: .\docker-manage.ps1 {command}" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Yellow
        Write-Host "  docker-up     - Start all services with Docker" -ForegroundColor White
        Write-Host "  docker-down   - Stop all Docker services" -ForegroundColor White
        Write-Host "  docker-clean  - Stop and remove all containers/volumes" -ForegroundColor White
        Write-Host "  local         - Switch to local development environment" -ForegroundColor White
        Write-Host "  docker-env    - Switch to Docker environment" -ForegroundColor White
        Write-Host "  migrate       - Run migrations in Docker container" -ForegroundColor White
        Write-Host "  shell         - Open Django shell in Docker container" -ForegroundColor White
        Write-Host "  logs          - Show Docker container logs" -ForegroundColor White
        Write-Host "  status        - Show status of Docker containers" -ForegroundColor White
        Write-Host ""
    }
}
