# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Company, Profile
#from .models import Company, ServiceFamily, ServiceType, ServiceCategory, Ticket

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating profile information"""
    class Meta:
        model = Profile
        fields = ['job_title', 'location', 'phone', 
                  'profile_picture','timezone', 'language',
                  'email_notifications']
class UserUpdateForm(forms.ModelForm):
    """Form for updating basic user information"""
    first_name = forms.CharField(max_length=150, required=True)  # Make sure required=True is set
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

#***********************************************#

#User = get_user_model()

class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'company', 'is_staff')
        # You might want to use a different widget for the company field
        # forms.Select(queryset=Company.objects.all())

class CompanyCreationForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ('name', 'slug', 'address', 'phone', 'is_active')