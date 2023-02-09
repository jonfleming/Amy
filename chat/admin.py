from django.contrib import admin
from .models import Utterance, Response


class UtteranceAdmin(admin.ModelAdmin):
    fields = ['time', 'utterance_text']
    list_display = ('utterance_text', 'time')


admin.site.register(Utterance, UtteranceAdmin)
admin.site.register(Response)
