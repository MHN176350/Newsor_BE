# Manual migration to fix notification model
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_news_content_articleimage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Rename type to notification_type
        migrations.RenameField(
            model_name='notification',
            old_name='type',
            new_name='notification_type',
        ),
        
        # Remove read_duration from readinghistory
        migrations.RemoveField(
            model_name='readinghistory',
            name='read_duration',
        ),
        
        # Add missing fields to notification
        migrations.AddField(
            model_name='notification',
            name='article',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='api.news'),
        ),
        migrations.AddField(
            model_name='notification',
            name='comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='api.comment'),
        ),
        migrations.AddField(
            model_name='notification',
            name='read_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='title',
            field=models.CharField(max_length=200, default='Notification'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notification',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Alter field content on news (to ensure it's TextField)
        migrations.AlterField(
            model_name='news',
            name='content',
            field=models.TextField(),
        ),
        
        # Create indexes
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read', 'created_at'], name='api_notific_recipie_535048_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['notification_type', 'created_at'], name='api_notific_notific_4e79a9_idx'),
        ),
    ]
