from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from accounts.models import User, Company

# Service hierarchy models (Family -> Type -> Category)
class ServiceFamily(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='service_families')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Service Families"
        ordering = ['name']
        unique_together = ['name', 'company']
    
    def __str__(self):
        return f"{self.name} ({self.company.name})"
class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    family = models.ForeignKey(ServiceFamily, on_delete=models.CASCADE, related_name='service_types')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'family']
    
    def __str__(self):
        return f"{self.name} ({self.family.name})"
    
class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['name']
        unique_together = ['name', 'service_type']
    
    def __str__(self):
        return f"{self.name} ({self.service_type.name})"

class Ticket(models.Model):
    """Main Ticket model with core ticket information"""
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    IMPACT = [
        ('DEPARTMENT', 'Department'),
        ('SERVICE', 'Service'),
        ('PERSON', 'Person'),
    ]
    PRIORITY = [
        ('CRITICAL', 'Critical'),
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    # Core ticket fields
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    impact = models.CharField(max_length=20, choices=IMPACT, default='Person')
    priority = models.CharField(max_length=20, choices=PRIORITY, default='MEDIUM')
    
    # Foreign keys
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null = True, blank = True,related_name="company_tickets")
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name="tickets")
    #impact = models.ForeignKey(ImpactLevel, on_delete=models.SET_NULL, 
    #                          null=True, blank=True, related_name="tickets")
    #priority = models.ForeignKey(PriorityLevel, on_delete=models.SET_NULL, 
     #                           null=True, blank=True, related_name="tickets")
    
    # User assignments
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, related_name="created_tickets")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name="assigned_tickets")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # When setting a ticket to resolved, update the resolved_at timestamp
        if self.status == 'RESOLVED' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"#{self.id} - {self.title}"

'''
class TicketAttachment(models.Model):
    """Model for ticket attachments"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to='ticket_attachments/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    size = models.PositiveIntegerField(blank=True, null=True)  # Size in bytes
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment: {self.filename} (Ticket #{self.ticket.id})"


class TicketComment(models.Model):
    """Model for comments on tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_internal = models.BooleanField(default=False)  # To differentiate between customer-visible and internal notes
    
    def __str__(self):
        return f"Comment on Ticket #{self.ticket.id} by {self.created_by}"
    
    class Meta:
        ordering = ['created_at']


class TicketHistory(models.Model):
    """Model to track changes to tickets for audit and tracking purposes"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Change to {self.field_changed} on Ticket #{self.ticket.id}"
    
    class Meta:
        verbose_name_plural = "Ticket Histories"
        ordering = ['-changed_at']'''