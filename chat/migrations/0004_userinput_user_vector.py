# Generated by Django 4.1 on 2023-04-17 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_amyprompt_amyresponse_userinput_profile_chat_mode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinput',
            name='user_vector',
            field=models.CharField(default='', max_length=50000),
        ),
    ]
