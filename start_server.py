"""
Django development server with WebSocket support.
Run this script to start the server with both HTTP and WebSocket capabilities.
"""
import sys
import subprocess
from pathlib import Path

def check_redis_connection():
    """Check if Redis is running."""
    try:
        import redis
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running on 127.0.0.1:6379")
        return False

def run_migrations():
    """Run Django migrations."""
    try:
        print("🔄 Running migrations...")
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("✅ Migrations completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        return False

def collect_static():
    """Collect static files."""
    try:
        print("📦 Collecting static files...")
        subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], check=True)
        print("✅ Static files collected")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Static files collection failed: {e}")
        return True  # Non-critical error

def start_server(port=8000):
    """Start Django server with ASGI support for WebSockets."""
    try:
        print(f"🚀 Starting Django server with WebSocket support on port {port}...")
        print(f"📡 HTTP: http://localhost:{port}/")
        print(f"🔌 WebSocket: ws://localhost:{port}/graphql/")
        print(f"📊 GraphQL Playground: http://localhost:{port}/graphql/")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Check if running in Docker (skip Redis check in Docker)
        import os
        is_docker = os.environ.get('DATABASE_HOST') == 'db'
        
        if is_docker:
            print("🐳 Docker environment detected, using optimized settings...")
            # In Docker, use daphne directly for better performance
            cmd = [
                sys.executable, "-m", "daphne",
                "-p", str(port),
                "-b", "0.0.0.0",
                "newsor.asgi:application"
            ]
        else:
            # Local development, use daphne with verbose output
            cmd = [
                sys.executable, "-m", "daphne",
                "-p", str(port),
                "-b", "0.0.0.0",
                "-v", "2",  # Verbose logging for development
                "newsor.asgi:application"
            ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        print("💡 Trying fallback with Django runserver...")
        
        # Fallback to regular Django runserver (no WebSocket support)
        try:
            subprocess.run([
                sys.executable, "manage.py", "runserver", 
                f"0.0.0.0:{port}"
            ])
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")

def main():
    """Main function."""
    import os
    is_docker = os.environ.get('DATABASE_HOST') == 'db'
    
    print("🔧 Django WebSocket Server Startup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ manage.py not found. Please run this script from the Django project root.")
        sys.exit(1)
    
    # Check Redis connection (skip in Docker as it's handled by docker-compose)
    if not is_docker:
        if not check_redis_connection():
            response = input("Continue without Redis? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print("🐳 Skipping Redis check in Docker environment")
    
    # Run migrations (skip in Docker as it's handled by entrypoint)
    if not is_docker:
        if not run_migrations():
            response = input("Continue with migration errors? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print("🐳 Skipping migrations in Docker environment (handled by entrypoint)")
    
    # Collect static files (skip in Docker as it's handled by Dockerfile)
    if not is_docker:
        collect_static()
    else:
        print("🐳 Skipping static files collection in Docker environment")
    
    # Get port from command line or use default
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    # Start server
    start_server(port)

if __name__ == "__main__":
    main()
