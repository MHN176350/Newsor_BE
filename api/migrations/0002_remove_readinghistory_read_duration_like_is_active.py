# Generated by Django 5.2.3 on 2025-07-07 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='readinghistory',
            name='read_duration',
        ),
        migrations.AddField(
            model_name='like',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
