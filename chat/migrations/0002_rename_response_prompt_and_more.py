# Generated by Django 4.1 on 2023-03-04 03:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Response',
            new_name='Prompt',
        ),
        migrations.RenameField(
            model_name='prompt',
            old_name='response_text',
            new_name='prompt_text',
        ),
    ]
