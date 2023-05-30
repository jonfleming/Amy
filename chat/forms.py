from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# Create your forms here.

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user


class ProfileForm(forms.Form):
    chat_modes = (
        ('converse', 'Converse - Ask questions to create a story'),
        ('friend', 'Friend - Sympathetic ear provides advice'),
        ('partner', 'Helper - What can I do to help?'),
        ('coach', 'Coach - Help with achieving goals'),
    )
    username = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    display_name = forms.CharField()
    chat_mode = forms.ChoiceField(widget=forms.Select, choices=chat_modes)
    about_you = forms.CharField(widget=forms.Textarea(), required=False)
