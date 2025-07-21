import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings

User = get_user_model()

class GraphQLSubscriptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Ban đầu chưa có user, join nhóm anonymous tạm thời
        self.user = AnonymousUser()
        self.group_name = 'notifications_anonymous'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        subprotocols = self.scope.get('subprotocols', [])
        if 'graphql-transport-ws' in subprotocols:
            chosen_subprotocol = 'graphql-transport-ws'
        elif 'graphql-ws' in subprotocols:
            chosen_subprotocol = 'graphql-ws'
        else:
            chosen_subprotocol = None

        if chosen_subprotocol:
            await self.accept(subprotocol=chosen_subprotocol)
        else:
            await self.close()
            return
        
        # Gửi connection_ack trong receive khi xử lý connection_init, nên ở đây không gửi

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            message = json.loads(text_data)
            message_type = message.get('type')

            if message_type == 'connection_init':
                payload = message.get('payload') or {}
                token = None
                
                # Token có thể ở dưới nhiều dạng, ví dụ:
                # {Authorization: 'Bearer <token>'} hoặc {authorization: 'Bearer <token>'} hoặc trực tiếp token
                for key in ['Authorization', 'authorization']:
                    if key in payload:
                        auth_header = payload[key]
                        if auth_header.startswith('Bearer '):
                            token = auth_header[7:]
                            break
                
                if not token:
                    # Nếu token không có thì để anonymous (hoặc có thể close connection)
                    self.user = AnonymousUser()
                else:
                    # Xác thực token và lấy user
                    try:
                        payload_data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                        username = payload_data.get('username')
                        user = await self.get_user(username)
                        if user and user.is_active:
                            self.user = user
                            # Thoát nhóm anonymous cũ
                            await self.channel_layer.group_discard(self.group_name, self.channel_name)
                            # Join nhóm notifications theo username
                            self.group_name = f'notifications_{self.user.username}'
                            await self.channel_layer.group_add(self.group_name, self.channel_name)
                        else:
                            self.user = AnonymousUser()
                    except Exception as e:
                        print(f"JWT decode error: {e}")
                        self.user = AnonymousUser()

                # Gửi connection_ack sau khi xử lý token
                await self.send(text_data=json.dumps({'type': 'connection_ack'}))

            elif message_type == 'subscribe':
                # Xử lý subscribe nếu cần
                self.subscription_id = message.get('id')
                # Bạn có thể gửi payload trả về nếu muốn
                
            elif message_type == 'complete':
                self.subscription_id = None
                
            # Xử lý message khác nếu có

        except json.JSONDecodeError:
            print("❗ JSON decode error in WebSocket receive()")

    async def notification_message(self, event):
        if hasattr(self, 'subscription_id') and self.subscription_id:
            await self.send(text_data=json.dumps({
                'type': 'next',
                'id': self.subscription_id,
                'payload': {
                    'data': {
                        'notificationAdded': event['notification']
                    }
                }
            }))

    @database_sync_to_async
    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None