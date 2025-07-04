# Merged migration combining all operations from 0004-0011

import cloudinary.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_remove_comment_moderated_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add ArticleImage model and alter News content
        migrations.CreateModel(
            name='ArticleImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', cloudinary.models.CloudinaryField(max_length=255, verbose_name='article_content_image')),
                ('alt_text', models.CharField(blank=True, max_length=255)),
                ('caption', models.CharField(blank=True, max_length=500)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='embedded_images', to='api.news')),
            ],
            options={
                'ordering': ['order', 'created_at'],
            },
        ),
        
        # Alter News content field
        migrations.AlterField(
            model_name='news',
            name='content',
            field=models.TextField(),
        ),
        
        # Add is_active to Like model
        migrations.AddField(
            model_name='like',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        
        # Add is_active to Tag model
        migrations.AddField(
            model_name='tag',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        
        # Increase CloudinaryField max_length to 500
        migrations.AlterField(
            model_name='userprofile',
            name='avatar',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=500, null=True, verbose_name='avatar'),
        ),
        migrations.AlterField(
            model_name='news',
            name='featured_image',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=500, null=True, verbose_name='news_image'),
        ),
        migrations.AlterField(
            model_name='articleimage',
            name='image',
            field=cloudinary.models.CloudinaryField(max_length=500, verbose_name='article_content_image'),
        ),
        
        # Remove comment like_count and add is_approved
        migrations.RemoveField(
            model_name='comment',
            name='like_count',
        ),
        migrations.AddField(
            model_name='comment',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
        
        # Alter comment content field
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.TextField(),
        ),
        
        # Add comment indexes
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['author', 'created_at'], name='api_comment_author__db6de2_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['parent', 'created_at'], name='api_comment_parent__d9e835_idx'),
        ),
        
        # Create Notification model
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('like', 'Like'), ('comment', 'Comment'), ('follow', 'Follow'), ('news', 'News')], max_length=20)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sent_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Add ReadingHistory read_duration field
        migrations.AddField(
            model_name='readinghistory',
            name='read_duration',
            field=models.PositiveIntegerField(default=0, help_text='Reading duration in seconds'),
        ),
    ]
