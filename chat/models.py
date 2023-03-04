import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from ast import literal_eval

class Profile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  display_name = models.CharField(max_length=100)
      
class Utterance(models.Model):
    user = models.CharField(max_length=128)
    utterance_text = models.CharField(max_length=8192)
    utterance_vector = models.CharField(max_length=50000, default='')
    utterance_time = models.DateTimeField('Time')

    def _embedding(self):
        return literal_eval(self.utterance_vector)

    embedding = property(_embedding)

    def __str__(self):
        return f"{self.user}: {self.utterance_text}"

    def is_recent(self):
        now = timezone.now()
        recent = now - datetime.timedelta(days=1) <= self.utterance_time <= now
        return recent


class Prompt(models.Model):
    utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)
    prompt_text = models.CharField(max_length=8192)

    def __str__(self):
        return self.prompt_text
