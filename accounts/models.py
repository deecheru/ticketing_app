# accounts/models.py
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