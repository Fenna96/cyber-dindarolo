# Generated by Django 3.0.5 on 2020-06-10 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_auto_20200610_1244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_image',
            field=models.ImageField(blank=True, default='static/profile_pics/default-avatar.jpg', upload_to='static/profile_pics/'),
        ),
    ]