from django.contrib.auth.models import User
from django.utils import timezone
from .models import News, Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


class NotificationService:
    """
    Service to handle notification creation and management
    """
    
    @staticmethod
    def notify_managers_of_submission(article):
        """
        Notify all managers when a writer submits an article for review
        """
        # Get all managers and admins
        managers = User.objects.filter(
            profile__role__in=['manager', 'admin'],
            is_active=True
        )
        
        notifications_created = []
        for manager in managers:
            notification = Notification.objects.create(
                recipient=manager,
                sender=article.author,
                notification_type='article_submitted',
                title=f'New Article Submitted: {article.title}',
                message=f'{article.author.get_full_name() or article.author.username} has submitted "{article.title}" for review.',
                article=article
            )
            notifications_created.append(notification)
            
            # Send real-time notification
            NotificationService._send_realtime_notification(manager.id, notification)
        
        return notifications_created
    
    @staticmethod
    def _send_realtime_notification(user_id, notification):
        """
        Send real-time notification via WebSocket
        """
        channel_layer = get_channel_layer()
        if channel_layer:
            # Serialize notification data
            notification_data = {
                'id': str(notification.id),
                'message': notification.message,
                'notificationType': notification.notification_type,
                'createdAt': notification.created_at.isoformat(),
                'article': {
                    'slug': notification.article.slug if notification.article else None
                } if notification.article else None
            }
            
            # Send to user's group
            group_name = f'notifications_{user_id}'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_message',
                    'notification': notification_data
                }
            )
    
    @staticmethod
    def notify_writer_of_approval(article, approved_by):
        """
        Notify writer when their article is approved
        """
        notification = Notification.objects.create(
            recipient=article.author,
            sender=approved_by,
            notification_type='article_approved',
            title=f'Article Approved: {article.title}',
            message=f'Your article "{article.title}" has been approved by {approved_by.get_full_name() or approved_by.username}.',
            article=article
        )
        
        # Send real-time notification
        NotificationService._send_realtime_notification(article.author.id, notification)
        
        return notification
    
    @staticmethod
    def notify_writer_of_rejection(article, rejected_by, rejection_reason=None):
        """
        Notify writer when their article is rejected
        """
        message = f'Your article "{article.title}" has been rejected by {rejected_by.get_full_name() or rejected_by.username}.'
        if rejection_reason:
            message += f' Reason: {rejection_reason}'
        
        notification = Notification.objects.create(
            recipient=article.author,
            sender=rejected_by,
            notification_type='article_rejected',
            title=f'Article Rejected: {article.title}',
            message=message,
            article=article
        )
        
        # Send real-time notification
        NotificationService._send_realtime_notification(article.author.id, notification)
        
        return notification
    
    @staticmethod
    def notify_writer_of_publication(article):
        """
        Notify writer when their article is published
        """
        notification = Notification.objects.create(
            recipient=article.author,
            notification_type='article_published',
            title=f'Article Published: {article.title}',
            message=f'Your article "{article.title}" has been published and is now live!',
            article=article
        )
        
        # Send real-time notification
        NotificationService._send_realtime_notification(article.author.id, notification)
        
        return notification
    
    @staticmethod
    def get_unread_notifications(user):
        """
        Get all unread notifications for a user
        """
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).select_related('sender', 'article', 'comment')
    
    @staticmethod
    def mark_notifications_as_read(user, notification_ids=None):
        """
        Mark notifications as read
        """
        queryset = Notification.objects.filter(recipient=user, is_read=False)
        
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        
        return queryset.update(is_read=True, read_at=timezone.now())
    
    @staticmethod
    def notify_admin_form_submission(contact):
        """
        Notify admin when a user submits a form for contact
        """
        # Get all admins
        managers = User.objects.filter(
            profile__role__in=['manager', 'admin'],
            is_active=True
        )
        
        notifications_created = []
        for manager in managers:
            notification = Notification.objects.create(
                recipient=manager,
                notification_type='system',
                title='New Form Submitted',
                message=f'{contact.name} has submitted  for contact.',
            )
            notifications_created.append(notification)
            
            # Send real-time notification
            NotificationService._send_realtime_notification_admin(manager.username, notification)
        
        return notifications_created
    
    @staticmethod
    def _send_realtime_notification_admin(username, notification):
        """
        Send real-time notification via WebSocket
        """
        channel_layer = get_channel_layer()
        if channel_layer:
            # Serialize notification data
            notification_data = {
                'id': str(notification.id),
                'message': notification.message,
                'notificationType': notification.notification_type,
                'createdAt': notification.created_at.isoformat(),
            }
            
            # Send to user's group
            group_name = f'notifications_{username}'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_message',
                    'notification': notification_data
                }
            )
