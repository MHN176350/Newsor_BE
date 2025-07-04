import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings

User = get_user_model()


class GraphQLSubscriptionConsumer(AsyncWebsocketConsumer):
    """
    Custom GraphQL Subscription Consumer for notifications
    """
    
    async def connect(self):
        print(f"WebSocket connection attempt from {self.scope.get('client', ['unknown', 'unknown'])[0]}")
        
        # Get token from connection params or headers
        token = None
        
        # Check subprotocols for token (graphql-ws protocol)
        subprotocols = self.scope.get('subprotocols', [])
        headers = dict(self.scope.get('headers', []))
        print(f"Subprotocols: {subprotocols}")
        print(f"Headers: {headers}")
        
        # Try to get token from Authorization header
        auth_header = headers.get(b'authorization', b'').decode()
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            print(f"Token from Authorization header: {token[:20]}..." if token else "No token")
        
        # If no token in headers, try query string
        if not token:
            query_string = self.scope.get('query_string', b'').decode()
            print(f"Query string: {query_string}")
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
                print(f"Token from query string: {token[:20]}..." if token else "No token")
        
        # For development, allow connections without tokens
        if not token:
            print("No token provided, allowing anonymous connection for development")
            self.user = AnonymousUser()
        else:
            # Verify JWT token
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                user = await self.get_user(user_id)
                
                if not user or not user.is_active:
                    print(f"Invalid user or inactive user: {user_id}")
                    await self.close()
                    return
                    
                self.user = user
                print(f"User authenticated: {user.username}")
                
            except (jwt.InvalidTokenError, User.DoesNotExist) as e:
                print(f"JWT token error: {e}")
                # For development, allow connection with anonymous user
                self.user = AnonymousUser()
        
        # Join user's notification group (use anonymous group for development)
        if hasattr(self.user, 'id') and self.user.id:
            self.group_name = f'notifications_{self.user.id}'
        else:
            self.group_name = 'notifications_anonymous'
            
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        print("Accepting WebSocket connection with subprotocol: graphql-ws")
        await self.accept(subprotocol='graphql-ws')
        
        # Send connection ack
        await self.send(text_data=json.dumps({
            'type': 'connection_ack'
        }))
        print("WebSocket connection established and ack sent")
        
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            # Leave notification group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages from client"""
        try:
            message = json.loads(text_data)
            message_type = message.get('type')
            
            if message_type == 'start':
                # Client starting a subscription
                payload = message.get('payload', {})
                query = payload.get('query', '')
                
                # Check if it's a notification subscription
                if 'notificationAdded' in query:
                    # Store subscription ID for this connection
                    self.subscription_id = message.get('id')
                    
                    # Send immediate response that subscription is active
                    await self.send(text_data=json.dumps({
                        'id': self.subscription_id,
                        'type': 'data',
                        'payload': {
                            'data': {
                                'notificationAdded': None
                            }
                        }
                    }))
                    
            elif message_type == 'stop':
                # Client stopping a subscription
                self.subscription_id = None
                
        except json.JSONDecodeError:
            pass
    
    async def notification_message(self, event):
        """Handle notification messages from group"""
        if hasattr(self, 'subscription_id') and self.subscription_id:
            await self.send(text_data=json.dumps({
                'id': self.subscription_id,
                'type': 'data',
                'payload': {
                    'data': {
                        'notificationAdded': event['notification']
                    }
                }
            }))
    
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
