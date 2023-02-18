from django.contrib import admin
from .models import Utterance, Response


class UtteranceAdmin(admin.ModelAdmin):
    fields = ['user', 'utterance_time', 'utterance_text']
    list_display = ('user', 'utterance_text', 'utterance_time')


admin.site.register(Utterance, UtteranceAdmin)
admin.site.register(Response)
