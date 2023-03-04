from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Utterance, Prompt, Profile


class UtteranceAdmin(admin.ModelAdmin):
    fields = ['user', 'utterance_time', 'utterance_text']
    list_display = ('user', 'utterance_text', 'utterance_time')

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
admin.site.register(Utterance, UtteranceAdmin)
admin.site.register(Prompt)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
