from django.core.management.base import BaseCommand
import asyncio
import websockets
import json
import time


class Command(BaseCommand):
    help = 'Monitor WebSocket connections for GraphQL subscriptions'

    def handle(self, *args, **options):
        self.stdout.write('Starting WebSocket monitor...')
        self.stdout.write('This will show WebSocket connection activity.')
        self.stdout.write('Press Ctrl+C to stop.')
        
        try:
            asyncio.run(self.monitor_websocket())
        except KeyboardInterrupt:
            self.stdout.write('\nMonitoring stopped.')

    async def monitor_websocket(self):
        uri = "ws://localhost:8000/graphql/"
        
        try:
            async with websockets.connect(
                uri, 
                subprotocols=['graphql-ws'],
                extra_headers={'Authorization': 'Bearer test-token'}
            ) as websocket:
                self.stdout.write(f"Connected to {uri}")
                
                # Send connection init
                await websocket.send(json.dumps({
                    'type': 'connection_init'
                }))
                
                # Listen for messages
                async for message in websocket:
                    data = json.loads(message)
                    timestamp = time.strftime("%H:%M:%S")
                    self.stdout.write(f"[{timestamp}] Received: {data}")
                    
        except Exception as e:
            self.stdout.write(f"WebSocket connection failed: {e}")
