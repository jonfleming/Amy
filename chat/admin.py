from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, AmyPrompt, UserInput, AmyResponse

class UserInputInline(admin.TabularInline):
    model = UserInput

class AmyPromptAdmin(admin.ModelAdmin):
    fields = ['amy_text', 'messages']
    list_display = ('amy_text', 'messages')
    inlines = [UserInputInline]

class UserInputAdmin(admin.ModelAdmin):
    fields = ['user', 'amy_prompt', 'created_at', 'user_text']
    list_display = ('user', 'user_text', 'created_at', 'amy_prompt')
    list_filter = ('user',)

class AmyResponseAdmin(admin.ModelAdmin):
    fields = ['user_input', 'amy_text']
    list_display = ('user_input', 'amy_text')

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
admin.site.register(AmyPrompt, AmyPromptAdmin)
admin.site.register(UserInput, UserInputAdmin)
admin.site.register(AmyResponse, AmyResponseAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
