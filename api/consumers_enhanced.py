"""
Enhanced WebSocket consumer with better error handling and connection management.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings
from urllib.parse import parse_qs

User = get_user_model()
logger = logging.getLogger(__name__)


class GraphQLSubscriptionConsumer(AsyncWebsocketConsumer):
    """
    Enhanced GraphQL Subscription Consumer with better connection handling.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.groups = []
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            logger.info("WebSocket connection attempt started")
            
            # Extract user authentication
            self.user = await self.get_user_from_token()
            
            # Accept the connection
            await self.accept(subprotocol='graphql-ws')
            
            # Join user-specific group if authenticated
            if self.user and not self.user.is_anonymous:
                group_name = f"user_{self.user.id}"
                await self.channel_layer.group_add(group_name, self.channel_name)
                self.groups.append(group_name)
                logger.info(f"User {self.user.username} connected to WebSocket")
            else:
                # Join anonymous group for public notifications
                group_name = "anonymous_users"
                await self.channel_layer.group_add(group_name, self.channel_name)
                self.groups.append(group_name)
                logger.info("Anonymous user connected to WebSocket")
            
            # Send connection acknowledgment
            await self.send(text_data=json.dumps({
                'type': 'connection_ack',
                'payload': {
                    'message': 'Connected successfully',
                    'authenticated': not self.user.is_anonymous if self.user else False
                }
            }))
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Leave all groups
            for group_name in self.groups:
                await self.channel_layer.group_discard(group_name, self.channel_name)
            
            user_info = f"User {self.user.username}" if self.user and not self.user.is_anonymous else "Anonymous user"
            logger.info(f"{user_info} disconnected from WebSocket (code: {close_code})")
            
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {e}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start':
                # Handle GraphQL subscription start
                await self.handle_subscription_start(data)
            elif message_type == 'stop':
                # Handle subscription stop
                await self.handle_subscription_stop(data)
            elif message_type == 'connection_init':
                # Handle connection initialization
                await self.handle_connection_init(data)
            elif message_type == 'ping':
                # Handle ping for keep-alive
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'payload': {'message': 'Invalid JSON format'}
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'payload': {'message': 'Internal server error'}
            }))
    
    async def handle_connection_init(self, data):
        """Handle connection initialization with authentication."""
        try:
            payload = data.get('payload', {})
            
            # Check for authorization token in payload
            auth_token = payload.get('Authorization') or payload.get('authorization')
            if auth_token:
                if auth_token.startswith('Bearer '):
                    auth_token = auth_token[7:]
                
                # Re-authenticate with the provided token
                user = await self.authenticate_token(auth_token)
                if user:
                    self.user = user
                    
                    # Update groups
                    for group_name in self.groups:
                        await self.channel_layer.group_discard(group_name, self.channel_name)
                    self.groups.clear()
                    
                    group_name = f"user_{self.user.id}"
                    await self.channel_layer.group_add(group_name, self.channel_name)
                    self.groups.append(group_name)
            
            # Send connection acknowledgment
            await self.send(text_data=json.dumps({
                'type': 'connection_ack',
                'payload': {
                    'authenticated': not self.user.is_anonymous if self.user else False
                }
            }))
            
        except Exception as e:
            logger.error(f"Connection init error: {e}")
            await self.send(text_data=json.dumps({
                'type': 'connection_error',
                'payload': {'message': 'Authentication failed'}
            }))
    
    async def handle_subscription_start(self, data):
        """Handle GraphQL subscription start."""
        try:
            subscription_id = data.get('id')
            query = data.get('payload', {}).get('query', '')
            
            # For now, just acknowledge the subscription
            # In a full implementation, you'd parse and execute the GraphQL subscription
            await self.send(text_data=json.dumps({
                'type': 'data',
                'id': subscription_id,
                'payload': {
                    'data': {
                        'message': 'Subscription started successfully'
                    }
                }
            }))
            
        except Exception as e:
            logger.error(f"Subscription start error: {e}")
    
    async def handle_subscription_stop(self, data):
        """Handle subscription stop."""
        subscription_id = data.get('id')
        await self.send(text_data=json.dumps({
            'type': 'complete',
            'id': subscription_id
        }))
    
    async def get_user_from_token(self):
        """Extract and authenticate user from WebSocket connection."""
        try:
            token = None
            
            # Method 1: Check subprotocols (graphql-ws)
            subprotocols = self.scope.get('subprotocols', [])
            if 'graphql-ws' in subprotocols:
                logger.info("GraphQL-WS protocol detected")
            
            # Method 2: Check headers
            headers = dict(self.scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                logger.info("Token found in Authorization header")
            
            # Method 3: Check query string
            if not token:
                query_string = self.scope.get('query_string', b'').decode()
                if query_string:
                    params = parse_qs(query_string)
                    if 'token' in params:
                        token = params['token'][0]
                        logger.info("Token found in query string")
            
            # Method 4: Check path parameters
            if not token:
                path = self.scope.get('path', '')
                if '/ws/' in path and '?' in path:
                    query_part = path.split('?')[1]
                    params = parse_qs(query_part)
                    if 'token' in params:
                        token = params['token'][0]
                        logger.info("Token found in path parameters")
            
            if token:
                user = await self.authenticate_token(token)
                if user:
                    return user
            
            # Return anonymous user if no valid token
            logger.info("No valid token found, using anonymous user")
            return AnonymousUser()
            
        except Exception as e:
            logger.error(f"Token extraction error: {e}")
            return AnonymousUser()
    
    @database_sync_to_async
    def authenticate_token(self, token):
        """Authenticate JWT token and return user."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if user_id:
                user = User.objects.get(id=user_id)
                if user.is_active:
                    return user
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except User.DoesNotExist:
            logger.warning(f"User not found for token")
            return None
        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return None
    
    # Group message handlers
    async def notification_message(self, event):
        """Handle notification messages sent to the group."""
        try:
            await self.send(text_data=json.dumps({
                'type': 'data',
                'payload': {
                    'data': {
                        'notification': event['notification']
                    }
                }
            }))
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def news_update(self, event):
        """Handle news update messages."""
        try:
            await self.send(text_data=json.dumps({
                'type': 'data',
                'payload': {
                    'data': {
                        'newsUpdate': event['news']
                    }
                }
            }))
        except Exception as e:
            logger.error(f"Error sending news update: {e}")
    
    async def user_status_update(self, event):
        """Handle user status updates."""
        try:
            await self.send(text_data=json.dumps({
                'type': 'data',
                'payload': {
                    'data': {
                        'userStatusUpdate': event['status']
                    }
                }
            }))
        except Exception as e:
            logger.error(f"Error sending user status update: {e}")


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Simple notification-only WebSocket consumer.
    Use this as an alternative if GraphQL subscriptions are too complex.
    """
    
    async def connect(self):
        """Accept WebSocket connection for notifications."""
        await self.accept()
        
        # Join notification group
        await self.channel_layer.group_add("notifications", self.channel_name)
        logger.info("Client connected to notifications WebSocket")
    
    async def disconnect(self, close_code):
        """Handle disconnect."""
        await self.channel_layer.group_discard("notifications", self.channel_name)
        logger.info(f"Client disconnected from notifications (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle incoming messages."""
        try:
            data = json.loads(text_data)
            # Echo back for testing
            await self.send(text_data=json.dumps({
                'type': 'echo',
                'message': f"Received: {data}"
            }))
        except Exception as e:
            logger.error(f"Notification consumer error: {e}")
    
    async def send_notification(self, event):
        """Send notification to client."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))
