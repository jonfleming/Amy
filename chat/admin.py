from django.contrib import admin

from .models import Utterance, Response

admin.site.register(Utterance)
admin.site.register(Response)