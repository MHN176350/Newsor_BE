from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import News, Notification
from api.notification_service import NotificationService


class Command(BaseCommand):
    help = 'Test real-time notifications by creating a sample notification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to send test notification to',
            required=True
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} does not exist')
            )
            return

        # Create a test notification
        notification = Notification.objects.create(
            recipient=user,
            notification_type='article_published',
            title='Test Notification',
            message=f'This is a test real-time notification for {user.username}!',
        )

        # Send real-time notification
        NotificationService._send_realtime_notification(user.id, notification)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent test notification to {user.username} (ID: {user.id})'
            )
        )
        self.stdout.write(f'Notification ID: {notification.id}')
        self.stdout.write(f'Message: {notification.message}')
