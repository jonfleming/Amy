from django.contrib import admin
from .models import Utterance, Response


class UtteranceAdmin(admin.ModelAdmin):
    fields = ['utterance_time', 'utterance_text']
    list_display = ('utterance_text', 'utterance_time')


admin.site.register(Utterance, UtteranceAdmin)
admin.site.register(Response)
