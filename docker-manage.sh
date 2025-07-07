#!/bin/bash

# Docker Environment Management Script for Newsor

case "$1" in
    "docker-up")
        echo "🐳 Starting Newsor with Docker (PostgreSQL + Redis containers)..."
        cp .env.docker .env 2>/dev/null || echo "Using current .env file"
        docker-compose up --build
        ;;
    "docker-down")
        echo "🛑 Stopping Docker containers..."
        docker-compose down
        ;;
    "docker-clean")
        echo "🧹 Cleaning up Docker containers and volumes..."
        docker-compose down -v
        docker system prune -f
        ;;
    "local")
        echo "💻 Switching to local development environment..."
        cp .env.local .env
        echo "Environment switched to local. Start your local PostgreSQL and Redis services."
        ;;
    "docker-env")
        echo "🐳 Switching to Docker environment..."
        cp .env.docker .env 2>/dev/null || echo "Docker .env file not found, using current .env"
        ;;
    "migrate")
        echo "🔄 Running database migrations in Docker..."
        docker-compose exec web python manage.py migrate
        ;;
    "shell")
        echo "🐚 Opening Django shell in Docker container..."
        docker-compose exec web python manage.py shell
        ;;
    "logs")
        echo "📋 Showing Docker logs..."
        docker-compose logs -f
        ;;
    "status")
        echo "📊 Docker containers status:"
        docker-compose ps
        ;;
    *)
        echo "🚀 Newsor Docker Management Script"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  docker-up     - Start all services with Docker"
        echo "  docker-down   - Stop all Docker services"
        echo "  docker-clean  - Stop and remove all containers/volumes"
        echo "  local         - Switch to local development environment"
        echo "  docker-env    - Switch to Docker environment"
        echo "  migrate       - Run migrations in Docker container"
        echo "  shell         - Open Django shell in Docker container"
        echo "  logs          - Show Docker container logs"
        echo "  status        - Show status of Docker containers"
        echo ""
        ;;
esac
