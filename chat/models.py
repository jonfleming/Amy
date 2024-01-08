import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class AmyPrompt(models.Model):
    messages = models.CharField(max_length=8192)
    amy_text = models.CharField(max_length=8192)

    def __str__(self):
        return self.amy_text

  
class UserInput(models.Model):
    user = models.CharField(max_length=128)
    user_text = models.CharField(max_length=8192)
    user_vector = models.CharField(max_length=50000, default='')
    chat_mode = models.CharField(max_length=25)
    category = models.CharField(max_length=10)
    created_at = models.DateTimeField('Time')
    amy_prompt = models.ForeignKey(AmyPrompt, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user}: {self.user_text}"

    def is_recent(self):
        now = timezone.now()
        recent = now - datetime.timedelta(days=1) <= self.created_at <= now
        return recent
        
class AmyResponse(models.Model):
    user_input = models.ForeignKey(UserInput, on_delete=models.CASCADE)
    amy_text = models.CharField(max_length=8192)

    def __str__(self):
        return self.amy_text

class Category(models.Model):
    name = models.CharField(max_length=50)
    vector = models.CharField(max_length=50000, default='')

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100)
    chat_mode = models.CharField(max_length=25)
    about_you = models.CharField(max_length=8192)
    show_summary = models.BooleanField()


    