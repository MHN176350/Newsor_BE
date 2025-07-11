# Docker Setup for Newsor

This document explains how to run Newsor using Docker with PostgreSQL and Redis containers instead of local services.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Quick Start

1. **Start the application with Docker:**
   ```powershell
   # Using PowerShell management script
   .\docker-manage.ps1 docker-up
   
   # Or directly with docker-compose
   docker-compose up --build
   ```
   
   > ⚠️ **First Build Notice**: The initial build may take 3-5 minutes due to downloading and compiling dependencies. Subsequent builds will be much faster thanks to Docker layer caching.

2. **Access the application:**
   - API: http://localhost:8000
   - GraphQL Playground: http://localhost:8000/graphql
   - Admin: http://localhost:8000/admin (admin/admin123)

3. **Stop the application:**
   ```powershell
   .\docker-manage.ps1 docker-down
   ```

## Services

### PostgreSQL Database
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Database**: newsor_db
- **User**: newsor_user
- **Password**: newsor_password

### Redis Cache
- **Image**: redis:7-alpine
- **Port**: 6379
- **Used for**: WebSocket channels and caching

### Web Application
- **Port**: 8000
- **Framework**: Django with GraphQL
- **ASGI Server**: Daphne

## Management Commands

Use the PowerShell script `docker-manage.ps1` for easy management:

```powershell
# Start all services
.\docker-manage.ps1 docker-up

# Stop all services
.\docker-manage.ps1 docker-down

# Clean up (remove volumes and containers)
.\docker-manage.ps1 docker-clean

# Run database migrations
.\docker-manage.ps1 migrate

# Open Django shell
.\docker-manage.ps1 shell

# View logs
.\docker-manage.ps1 logs

# Check container status
.\docker-manage.ps1 status

# Switch to local development
.\docker-manage.ps1 local

# Switch back to Docker environment
.\docker-manage.ps1 docker-env
```

## Environment Files

- **`.env`**: Current environment configuration
- **`.env.docker`**: Docker-specific configuration
- **`.env.local`**: Local development configuration
- **`.env.example`**: Example configuration template

## Development Workflow

### Using Docker (Recommended)
1. Make sure Docker is running
2. Run `.\docker-manage.ps1 docker-up`
3. The application will be available at http://localhost:8000
4. Database and Redis are automatically configured

### Switching to Local Development
1. Run `.\docker-manage.ps1 local`
2. Start your local PostgreSQL and Redis services
3. Run the Django development server locally

## Database Migrations

Migrations are automatically run when starting the Docker container. The startup process includes:

1. **Database Connection Check** - Waits for PostgreSQL to be ready
2. **Run Migrations** - Applies any pending database migrations
3. **Create Superuser** - Creates admin user if it doesn't exist (admin/admin123)
4. **Populate Sample Data** - Loads initial sample data
5. **Update Email Templates** - Updates email templates from `update_email_template.py`
6. **Start Server** - Launches the Django application

To run migrations manually:

```powershell
.\docker-manage.ps1 migrate
```

## Troubleshooting

### Container Issues
```powershell
# Check container status
.\docker-manage.ps1 status

# View logs
.\docker-manage.ps1 logs

# Clean up and restart
.\docker-manage.ps1 docker-clean
.\docker-manage.ps1 docker-up
```

### Database Connection Issues
- Ensure PostgreSQL container is healthy
- Check that DATABASE_HOST=db in your .env file
- Verify database credentials match docker-compose.yml

### Redis Connection Issues
- Ensure Redis container is running
- Check that REDIS_URL=redis://redis:6379/0 in your .env file

## Production Considerations

For production deployment:
1. Change DEBUG=False in environment variables
2. Use proper secret keys
3. Configure proper ALLOWED_HOSTS
4. Use environment-specific docker-compose files
5. Set up proper SSL/TLS certificates
6. Configure proper backup strategies for PostgreSQL

## API Endpoints

- **GraphQL**: http://localhost:8000/graphql
- **REST API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin
- **WebSocket**: ws://localhost:8000/ws/

## Default Credentials

- **Admin User**: admin / admin123
- **Database**: newsor_user / newsor_password

## Performance Optimization

### Build Time Optimization

The initial Docker build can take 200+ seconds due to these heavy packages:
- `build-essential` (~200MB) - GCC compiler toolchain
- `libpq-dev` (~50MB) - PostgreSQL development libraries
- `netcat-openbsd` (~small) - Network connectivity testing

### Speed Up Builds:

1. **Use the optimized Dockerfile:**
   ```powershell
   # Rename current Dockerfile and use optimized version
   mv Dockerfile Dockerfile.original
   mv Dockerfile.optimized Dockerfile
   ```

2. **Enable Docker BuildKit (faster builds):**
   ```powershell
   # Add to your environment or run before docker commands
   $env:DOCKER_BUILDKIT=1
   docker-compose up --build
   ```

3. **Use Docker layer caching:**
   - After first build, subsequent builds are much faster
   - Only rebuilds when requirements.txt or source code changes

4. **Alternative: Use pre-built images:**
   ```yaml
   # In docker-compose.yml, you could use:
   web:
     image: python:3.13-slim
     # ... rest of config
   ```

### Reduce Image Size:

The optimized Dockerfile uses:
- **Multi-stage builds**: Separates build tools from runtime
- **Runtime-only packages**: `libpq5` instead of `libpq-dev` in final image
- **Cleanup commands**: Removes package caches and temporary files

**Image size comparison:**
- Original: ~800MB
- Optimized: ~400MB

### Development Tips:

```powershell
# Skip rebuild if no dependency changes
docker-compose up

# Force clean rebuild (slower but ensures fresh start)
.\docker-manage.ps1 docker-clean
.\docker-manage.ps1 docker-up

# Use cached layers for faster development
docker-compose up --build --parallel
```
