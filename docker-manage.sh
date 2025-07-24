#!/bin/bash

# Docker Environment Management Script for Newsor Backend
# Updated to work with start_server.py WebSocket configuration

case "$1" in
    "docker-up"|"dev")
        echo "🐳 Starting Newsor with Docker (Development with WebSocket support)..."
        echo "📦 Using start_server.py for enhanced WebSocket handling..."
        docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
        ;;
    "prod")
        echo "🚀 Starting Newsor in Production mode..."
        docker-compose -f docker-compose.yml up --build -d
        ;;
    "docker-down"|"stop")
        echo "🛑 Stopping Docker containers..."
        docker-compose down
        ;;
    "docker-clean"|"clean")
        echo "🧹 Cleaning up Docker containers and volumes..."
        docker-compose down -v
        docker system prune -f
        ;;
    "build")
        echo "🔨 Building Docker containers..."
        docker-compose build --no-cache
        ;;
    "logs")
        echo "� Showing Docker logs..."
        if [ -n "$2" ]; then
            docker-compose logs -f "$2"
        else
            docker-compose logs -f
        fi
        ;;
    "shell")
        echo "🐚 Opening shell in web container..."
        docker-compose exec web bash
        ;;
    "test")
        echo "🧪 Running tests in Docker..."
        docker-compose exec web python manage.py test
        ;;
    "test-websocket")
        echo "🔌 Testing WebSocket connection..."
        docker-compose exec web python test_websocket.py
        ;;
    "redis-test")
        echo "📡 Testing Redis connection..."
        docker-compose exec web python manage.py test_redis
        ;;
    "local")
        echo "� Switching to local development environment..."
        echo "⚠️  Make sure to start local PostgreSQL and Redis services."
        echo "🔌 Run 'python start_server.py' for WebSocket support"
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
        echo "🚀 Newsor Docker Management Script (WebSocket Enhanced)"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "🐳 Container Management:"
        echo "  dev|docker-up    - Start development environment with live reload & WebSocket support"
        echo "  prod             - Start production environment"
        echo "  stop|docker-down - Stop all Docker services"
        echo "  clean            - Stop and remove all containers/volumes"
        echo "  build            - Build all containers"
        echo ""
        echo "🔧 Development Tools:"
        echo "  logs [service]   - Show Docker container logs (optionally for specific service)"
        echo "  shell            - Open bash shell in web container"
        echo "  migrate          - Run database migrations in Docker container"
        echo "  test             - Run Django tests in Docker"
        echo "  test-websocket   - Test WebSocket connection"
        echo "  redis-test       - Test Redis connection and cache functionality"
        echo ""
        echo "💻 Local Development:"
        echo "  local            - Information for local development setup"
        echo ""
        echo "📊 Monitoring:"
        echo "  status           - Show status of Docker containers"
        echo ""
        echo "🔌 WebSocket Features:"
        echo "  - Enhanced WebSocket consumer with better connection handling"
        echo "  - Redis-backed real-time notifications"
        echo "  - GraphQL-WS protocol support"
        echo "  - JWT authentication for WebSocket connections"
        echo ""
        ;;
esac
