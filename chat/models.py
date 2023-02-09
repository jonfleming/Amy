import datetime
from django.db import models
from django.utils import timezone

# Create your models here.


class Utterance(models.Model):
    utterance_text = models.CharField(max_length=8192)
    time = models.DateTimeField('Time')

    def __str__(self):
        return self.utterance_text

    def is_recent(self):
        now = timezone.now()
        recent = now - datetime.timedelta(days=1) <= self.time <= now
        return recent


class Response(models.Model):
    utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)
    response_text = models.CharField(max_length=8192)

    def __str__(self):
        return self.response_text
