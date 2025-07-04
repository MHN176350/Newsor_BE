# Generated manually to fix CloudinaryField max_length issue

from django.db import migrations
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_news_content_articleimage'),
    ]

    operations = [
        # Alter UserProfile avatar field to remove max_length limit
        migrations.AlterField(
            model_name='userprofile',
            name='avatar',
            field=cloudinary.models.CloudinaryField(blank=True, null=True, verbose_name='avatar'),
        ),
        # Alter ArticleImage field to remove max_length limit
        migrations.AlterField(
            model_name='articleimage',
            name='image',
            field=cloudinary.models.CloudinaryField(verbose_name='article_content_image'),
        ),
        # Alter News featured_image field to remove max_length limit
        migrations.AlterField(
            model_name='news',
            name='featured_image',
            field=cloudinary.models.CloudinaryField(blank=True, null=True, verbose_name='news_image'),
        ),
    ]
