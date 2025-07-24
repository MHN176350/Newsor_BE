@echo off
REM Docker Environment Management Script for Newsor Backend (Windows)
REM Updated to work with start_server.py WebSocket configuration

if "%1"=="" goto usage
if "%1"=="help" goto usage

if "%1"=="dev" goto dev
if "%1"=="docker-up" goto dev
if "%1"=="prod" goto prod
if "%1"=="stop" goto stop
if "%1"=="docker-down" goto stop
if "%1"=="clean" goto clean
if "%1"=="docker-clean" goto clean
if "%1"=="build" goto build
if "%1"=="logs" goto logs
if "%1"=="shell" goto shell
if "%1"=="test" goto test
if "%1"=="test-websocket" goto test_websocket
if "%1"=="redis-test" goto redis_test
if "%1"=="migrate" goto migrate
if "%1"=="status" goto status
if "%1"=="local" goto local

goto usage

:dev
echo 🐳 Starting Newsor with Docker (Development with WebSocket support)...
echo 📦 Using start_server.py for enhanced WebSocket handling...
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
goto end

:prod
echo 🚀 Starting Newsor in Production mode...
docker-compose -f docker-compose.yml up --build -d
goto end

:stop
echo 🛑 Stopping Docker containers...
docker-compose down
goto end

:clean
echo 🧹 Cleaning up Docker containers and volumes...
docker-compose down -v
docker system prune -f
goto end

:build
echo 🔨 Building Docker containers...
docker-compose build --no-cache
goto end

:logs
echo 📄 Showing Docker logs...
if "%2"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f %2
)
goto end

:shell
echo 🐚 Opening shell in web container...
docker-compose exec web bash
goto end

:test
echo 🧪 Running tests in Docker...
docker-compose exec web python manage.py test
goto end

:test_websocket
echo 🔌 Testing WebSocket connection...
docker-compose exec web python test_websocket.py
goto end

:redis_test
echo 📡 Testing Redis connection...
docker-compose exec web python manage.py test_redis
goto end

:migrate
echo 🔄 Running database migrations in Docker...
docker-compose exec web python manage.py migrate
goto end

:status
echo 📊 Docker containers status:
docker-compose ps
goto end

:local
echo 💻 Switching to local development environment...
echo ⚠️  Make sure to start local PostgreSQL and Redis services.
echo 🔌 Run 'python start_server.py' for WebSocket support
goto end

:usage
echo 🚀 Newsor Docker Management Script (WebSocket Enhanced) - Windows
echo.
echo Usage: %0 {command}
echo.
echo 🐳 Container Management:
echo   dev^|docker-up    - Start development environment with live reload ^& WebSocket support
echo   prod             - Start production environment
echo   stop^|docker-down - Stop all Docker services
echo   clean            - Stop and remove all containers/volumes
echo   build            - Build all containers
echo.
echo 🔧 Development Tools:
echo   logs [service]   - Show Docker container logs (optionally for specific service)
echo   shell            - Open bash shell in web container
echo   migrate          - Run database migrations in Docker container
echo   test             - Run Django tests in Docker
echo   test-websocket   - Test WebSocket connection
echo   redis-test       - Test Redis connection and cache functionality
echo.
echo 💻 Local Development:
echo   local            - Information for local development setup
echo.
echo 📊 Monitoring:
echo   status           - Show status of Docker containers
echo.
echo 🔌 WebSocket Features:
echo   - Enhanced WebSocket consumer with better connection handling
echo   - Redis-backed real-time notifications
echo   - GraphQL-WS protocol support
echo   - JWT authentication for WebSocket connections
echo.

:end
