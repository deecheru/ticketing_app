# In your app's admin.py file
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Company, Profile


# Register the models with their admin classes
admin.site.register(User)
admin.site.register(Company)
admin.site.register(Profile)
