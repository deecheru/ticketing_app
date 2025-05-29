from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
from .notifications import send_ticket_creation_notification
from accounts.models import Profile


@receiver(post_save, sender=Ticket)
def ticket_post_save(sender, instance, created, **kwargs):
    """Signal handler to send notifications when a ticket is created"""
    if created :
        send_ticket_creation_notification(instance)