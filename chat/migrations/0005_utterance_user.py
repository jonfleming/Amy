# Generated by Django 4.1 on 2023-02-18 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_rename_utternace_vector_utterance_utterance_vector'),
    ]

    operations = [
        migrations.AddField(
            model_name='utterance',
            name='user',
            field=models.CharField(default='Jon', max_length=128),
            preserve_default=False,
        ),
    ]
