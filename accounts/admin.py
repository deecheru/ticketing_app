# In your app's admin.py file
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Company, Profile, StaffCompanyAssignment


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_company_agent', 'company')
    list_filter = ('is_staff', 'is_superuser', 'is_company_agent', 'company')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_company_agent', 'groups', 'user_permissions')}),
        ('Company', {'fields': ('company',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_company_agent', 'company'),
        }),
    )

    def get_inline_instances(self, request, obj=None):
        """Only include ProfileInline when editing an existing user (not when creating)."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')

class StaffCompanyAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'assigned_by', 'assigned_at')
    list_filter = ('company', 'assigned_by', 'assigned_at')
    search_fields = ('user__username', 'company__name')
    raw_id_fields = ('user', 'company', 'assigned_by')

# Register the models with their admin classes
admin.site.register(User,UserAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(StaffCompanyAssignment, StaffCompanyAssignmentAdmin)
admin.site.register(Profile)

