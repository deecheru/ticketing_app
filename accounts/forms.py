# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Company, Profile

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating profile information"""
    class Meta:
        model = Profile
        fields = ['role', 'job_title', 'department', 'phone', 
                  'profile_picture', 'bio', 'timezone', 'language',
                  'email_notifications']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
class UserUpdateForm(forms.ModelForm):
    """Form for updating basic user information"""
    first_name = forms.CharField(max_length=150, required=True)  # Make sure required=True is set
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']