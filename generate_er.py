def generate_mermaid_er(models):
    """Generates Mermaid ER diagram syntax from a list of Django model classes."""
    output = "erDiagram\n"
    relationships = []
    for model in models:
        model_name = model.__name__
        output += f"    {model_name} {{\n"
        for field in model._meta.get_fields():
            if not field.is_relation:
                field_type = field.get_internal_type()
                output += f"        {field_type} {field.name}\n"
            elif field.one_to_many:
                related_model_name = field.related_model.__name__
                relationships.append(f"    {model_name} ||--o{{ {related_model_name} : {field.name}")
            elif field.many_to_one:
                related_model_name = field.related_model.__name__
                relationships.append(f"    {related_model_name} ||--o{{ {model_name} : {field.name}")
            elif field.many_to_many:
                related_model_name = field.related_model.__name__
                relationships.append(f"    {model_name} ||--o{{ {related_model_name} : {field.name} (m:n)")
            elif field.one_to_one:
                related_model_name = field.related_model.__name__
                relationships.append(f"    {model_name} ||--o| {related_model_name} : {field.name}")
        output += "    }\n"

    for rel in relationships:
        output += f"{rel}\n"

    return output

if __name__ == '__main__':
    from django.db import models
    from django.conf import settings

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
        contacts = models.ManyToManyField(
            settings.AUTH_USER_MODEL,
            related_name='tagged_in_tickets',
            blank=True,  # Allow no contacts to be tagged
            help_text='Tag other users from your company who should be involved in this ticket.'
        )
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
        def get_extension(self):
            name, extension = os.path.splitext(self.filename)
            return extension.lower()


    class TicketComment(models.Model):
        """Model for comments on tickets"""
        ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
        text = models.TextField()
        created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        def __str__(self):
            return f"Comment on Ticket #{self.ticket.id} by {self.created_by}"
        
        class Meta:
            ordering = ['created_at']

    class User(AbstractUser):
        """Custom user model for multi-tenant authentication"""
        # Add custom fields
        company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, related_name='users',blank=True)
        
        # You could add more fields like:
        # role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
        # department = models.CharField(max_length=100, blank=True)

    

    class Profile(models.Model):
        """Extended profile information for users"""
        LANGUAGE_CHOICES = (
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('zh', 'Chinese'),
            ('ja', 'Japanese'),
            # Add more languages as needed
        )
        
        
        user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

        job_title = models.CharField(max_length=100, blank=True, null=True)
        location = models.CharField(max_length=100, blank=True, null=True)
        phone = models.CharField(max_length=20, blank=True, null=True)
        profile_picture = models.ImageField(upload_to='static/images/profile_pictures/', blank=True, null=True)
        
        # Additional fields you might consider
        timezone = models.CharField(max_length=50, default='UTC', blank=True)
        language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en',blank=True)
        
        # Notification preferences
        email_notifications = models.BooleanField(default=True)
        
        # Timestamps
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        def __str__(self):
            return f"{self.user.username}'s Profile"

    from django.utils import timezone
    import os

    models_to_diagram = [Company, User, Profile, ServiceFamily, ServiceType, ServiceCategory, Ticket, TicketAttachment, TicketComment]
    mermaid_syntax = generate_mermaid_er(models_to_diagram)
    print(mermaid_syntax)