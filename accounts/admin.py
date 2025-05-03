# In your app's admin.py file
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User,Company  # Import your custom User model

class CustomUserAdmin(UserAdmin):
    # The fields to be used in displaying the User model
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'company')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'company')
    
    # Fields for adding a user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    # Fields for editing a user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Company info'), {'fields': ('company',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

# Register the custom User model with the custom admin class
admin.site.register(User, CustomUserAdmin)

admin.site.register(Company)
