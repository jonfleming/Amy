from django.db import models

# Create your models here.

class Utterance(models.Model):
  utterance_text = models.CharField(max_length=8192)
  time = models.DateTimeField('Time')
  
class Response(models.Model):
  utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)
  response_text = models.CharField(max_length=8192)
  
  