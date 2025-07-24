#!/bin/bash

# WebSocket Debug Script
# This script helps diagnose WebSocket connection issues

echo "🔍 WebSocket Connection Diagnostic Tool"
echo "=================================="

# Check if containers are running
echo "📦 Checking Docker containers..."
docker-compose ps

echo ""
echo "🌐 Checking network connectivity..."

# Check if web server is responding
echo "Testing HTTP endpoint..."
curl -I http://192.168.1.36:8000/ 2>/dev/null && echo "✅ HTTP OK" || echo "❌ HTTP Failed"

echo ""
echo "🔌 Testing WebSocket endpoint..."

# Test WebSocket connection with different methods
echo "Testing WebSocket connection to ws://192.168.1.36:8000/graphql/"

# Method 1: Using netcat if available
if command -v nc >/dev/null; then
    echo "Testing with netcat..."
    timeout 5 nc -zv 192.168.1.36 8000 && echo "✅ Port 8000 is open" || echo "❌ Port 8000 is not accessible"
else
    echo "netcat not available, skipping port test"
fi

echo ""
echo "📋 Checking container logs..."
echo "Last 20 lines of web container logs:"
docker-compose logs --tail=20 web

echo ""
echo "🔧 WebSocket Configuration Check..."

# Check if the GraphQL endpoint is accessible
echo "Testing GraphQL endpoint..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { name } } }"}' \
  http://192.168.1.36:8000/graphql/ 2>/dev/null | jq . && echo "✅ GraphQL endpoint OK" || echo "❌ GraphQL endpoint failed"

echo ""
echo "🧪 Running internal WebSocket test..."
docker-compose exec web python test_network_websocket.py 192.168.1.36 8000 || echo "❌ Internal WebSocket test failed"

echo ""
echo "💡 TROUBLESHOOTING TIPS:"
echo "1. Make sure firewall allows port 8000"
echo "2. Check if containers are healthy: docker-compose ps"
echo "3. View real-time logs: docker-compose logs -f web"
echo "4. Test local connection: python test_websocket.py ws://localhost:8000/graphql/"
echo "5. Test network connection: python test_websocket.py ws://192.168.1.36:8000/graphql/"
