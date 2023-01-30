# Generated by Django 4.1 on 2023-01-30 00:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Utterance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('utterance_text', models.CharField(max_length=8192)),
                ('time', models.DateTimeField(verbose_name='Time')),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response_text', models.CharField(max_length=8192)),
                ('utterance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.utterance')),
            ],
        ),
    ]
