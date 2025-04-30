from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model for multi-tenant authentication"""
    # Add custom fields
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, related_name='users')
    
    # You could add more fields like:
    # role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
    # department = models.CharField(max_length=100, blank=True)

class Company(models.Model):
    """Company model for multi-tenant setup"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    """Extended profile information for users"""
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('client', 'Client'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    job_title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Additional fields you might consider
    timezone = models.CharField(max_length=50, default='UTC', blank=True)
    language = models.CharField(max_length=10, default='en', blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"