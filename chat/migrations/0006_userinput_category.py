# Generated by Django 4.1 on 2023-05-25 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinput',
            name='category',
            field=models.CharField(default='Story', max_length=10),
            preserve_default=False,
        ),
    ]