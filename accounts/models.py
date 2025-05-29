from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model for multi-tenant authentication"""
    # Add custom fields
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, related_name='users', blank=True)
    is_company_agent = models.BooleanField(default=False, help_text="Designates whether this user is a company agent with special privileges")
    
    class Meta:
        permissions = [
            ("can_manage_users", "Can manage users"),
            ("can_manage_tickets", "Can manage tickets"),
            ("can_manage_company", "Can manage company"),
            ("can_view_assigned_companies", "Can view tickets from assigned companies"),
            ("can_manage_assigned_tickets", "Can manage tickets from assigned companies"),
        ]
    
    def has_perm(self, perm, obj=None):
        # Superusers have all permissions
        if self.is_superuser:
            return True
        # Company agents have special permissions for their assigned companies
        if self.is_company_agent and obj and hasattr(obj, 'company'):
            if self.assigned_companies.filter(company=obj.company).exists():
                return True
        # Staff users have all permissions within their company
        if self.is_staff and obj and hasattr(obj, 'company'):
            return obj.company == self.company
        return super().has_perm(perm, obj)
    
    def has_module_perms(self, app_label):
        # Superusers have access to all modules
        if self.is_superuser:
            return True
        # Staff users and company agents have access to all modules
        if self.is_staff or self.is_company_agent:
            return True
        return super().has_module_perms(app_label)

class Company(models.Model):
    """Company model for multi-tenant setup"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    """Extended profile information for users"""
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.jpg')
    
    # Google Authenticator fields
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    mfa_verified = models.BooleanField(default=False)
    first_login_completed = models.BooleanField(default=False)
    
    job_title = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Additional fields
    timezone = models.CharField(max_length=50, default='UTC', blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en', blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    
    # Password reset fields
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token_created = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class StaffCompanyAssignment(models.Model):
    """Model to track which companies a user is assigned to"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_companies')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='company_assignments_made')

    class Meta:
        unique_together = ('user', 'company')
        verbose_name = 'Company Assignment'
        verbose_name_plural = 'Company Assignments'

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"