# Generated manually to fix CloudinaryField length limit

from django.db import migrations
import cloudinary.models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_fix_cloudinary_field_length'),
    ]

    operations = [
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
            field=cloudinary.models.CloudinaryField(max_length=500, verbose_name='article_image'),
        ),
    ]
