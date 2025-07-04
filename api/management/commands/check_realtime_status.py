from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from django.conf import settings
import redis


class Command(BaseCommand):
    help = 'Check real-time notification system status'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking Real-time Notification System Status...\n')
        
        # Check Django Channels
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                self.stdout.write(
                    self.style.SUCCESS('✅ Django Channels: Configured')
                )
                self.stdout.write(f'   Backend: {channel_layer.__class__.__name__}')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Django Channels: Not configured')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Django Channels: Error - {e}')
            )

        # Check Redis connection
        try:
            r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
            r.ping()
            self.stdout.write(
                self.style.SUCCESS('✅ Redis: Connected and responding')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Redis: Connection failed - {e}')
            )
            self.stdout.write('   Note: Redis is required for real-time features')

        # Check ASGI configuration
        asgi_app = getattr(settings, 'ASGI_APPLICATION', None)
        if asgi_app:
            self.stdout.write(
                self.style.SUCCESS(f'✅ ASGI: Configured ({asgi_app})')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ ASGI: Not configured')
            )

        # Check GraphQL schema
        try:
            from api.schema import schema
            subscription_type = schema.get_subscription_type()
            if subscription_type:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ GraphQL Subscriptions: Schema configured ({subscription_type})')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ GraphQL Subscriptions: Not in schema')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ GraphQL Schema: Error - {e}')
            )

        self.stdout.write('\n📋 System Summary:')
        self.stdout.write('   • Backend: Django + Channels + GraphQL')
        self.stdout.write('   • WebSocket endpoint: ws://localhost:8000/graphql/')
        self.stdout.write('   • Frontend: Apollo Client with split link')
        self.stdout.write('   • Authentication: JWT tokens in WebSocket connection')
        
        self.stdout.write('\n🧪 To test the system:')
        self.stdout.write('   1. Start Django server: python manage.py runserver')
        self.stdout.write('   2. Start frontend: npm run dev')
        self.stdout.write('   3. Login to frontend')
        self.stdout.write('   4. Run: python manage.py test_notifications --user-id <your-user-id>')
        self.stdout.write('   5. Check frontend notification bell for real-time updates')
