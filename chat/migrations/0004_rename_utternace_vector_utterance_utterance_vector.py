# Generated by Django 4.1 on 2023-02-12 08:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_alter_utterance_utternace_vector'),
    ]

    operations = [
        migrations.RenameField(
            model_name='utterance',
            old_name='utternace_vector',
            new_name='utterance_vector',
        ),
    ]