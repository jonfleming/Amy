from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, AmyPrompt, UserInput, AmyResponse

class UserInputAdmin(admin.ModelAdmin):
    fields = ['user', 'created_at', 'user_text']
    list_display = ('user', 'user_text', 'created_at')

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
admin.site.register(UserInput, UserInputAdmin)
admin.site.register(AmyPrompt)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
