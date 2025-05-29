# notifications.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_ticket_creation_notification(ticket):
    """
    Send email notifications when a ticket is created to:
    1. The creator
    2. The assigned person (if any)
    3. All tagged contacts
    """
    # Collect all recipients
    recipients = []
    
    # Add creator's email
    if ticket.created_by and ticket.created_by.email:
        recipients.append(ticket.created_by.email)
    
    # Add assignee's email if present
    if ticket.assigned_to and ticket.assigned_to.email:
        recipients.append(ticket.assigned_to.email)
    
    # Add all tagged contacts' emails
    for contact in ticket.contacts.all():
        if contact.email and contact.email not in recipients:
            recipients.append(contact.email)
    
    # Remove duplicates
    recipients = list(set(recipients))
    
    if not recipients:
        return False  # No one to notify
    
    # Prepare email content
    subject = f"[{ticket.company.name}] New Ticket: {ticket.title}"
    
    # Context for the email template
    context = {
        'ticket': ticket,
        'company': ticket.company,
        'ticket_url': f"{settings.SITE_URL}/user_tickets/{ticket.id}/",
    }
    
    # Render HTML and plain text versions
    html_content = render_to_string('emails/ticket_created.html', context)
    text_content = strip_tags(html_content)
    
    # Create and send the email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    
    return True

def send_new_comment_notification(comment):
    ticket = comment.ticket
    subject = f"[{ticket.company.name}] New Comment on Ticket: {ticket.title}"
    recipients = set()
    if ticket.created_by and ticket.created_by.email:
        recipients.add(ticket.created_by.email)
    if ticket.assigned_to and ticket.assigned_to.email and ticket.assigned_to != comment.created_by:
        recipients.add(ticket.assigned_to.email)
    for contact in ticket.contacts.all():
        if contact.email and contact != comment.created_by:
            recipients.add(contact.email)

    if recipients:
        context = {
            'comment': comment,
            'ticket': ticket,
            'ticket_url': f"{settings.SITE_URL}/user_tickets/{ticket.id}/",
        }
        html_content = render_to_string('emails/ticket_new_comment.html', context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, list(recipients))
        msg.attach_alternative(html_content, "text/html")
        msg.send()
def send_ticket_updated_notification(ticket, updated_by, changes=None, attachments=None):
    """
    Send email notifications when a ticket is updated to:
    1. The creator
    2. The assigned person (if any)
    3. All tagged contacts
    4. The person who made the update (optional, we'll exclude them by default)
    """
    recipients = set()

    # Add creator's email
    if ticket.created_by and ticket.created_by.email:
        recipients.add(ticket.created_by.email)

    # Add assignee's email if present and not the updater
    if ticket.assigned_to and ticket.assigned_to.email and ticket.assigned_to != updated_by:
        recipients.add(ticket.assigned_to.email)

    # Add all tagged contacts' emails if not the updater
    for contact in ticket.contacts.all():
        if contact.email and contact != updated_by:
            recipients.add(contact.email)

    if not recipients:
        return False  # No one to notify

    subject = f"[{ticket.company.name}] Ticket Updated: {ticket.title}"

    context = {
        'ticket': ticket,
        'company': ticket.company,
        'updated_by': updated_by,
        'changes': changes or {},  # Ensure changes is at least an empty dict
        'attachments': attachments,
        'ticket_url': f"{settings.SITE_URL}/user_tickets/{ticket.id}/",
    }

    html_content = render_to_string('emails/ticket_updated.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(recipients)
    )
    email.attach_alternative(html_content, "text/html")
    
    # Actually send the email
    try:
        email.send()
        return True
    except Exception as e:
        # Log the error for debugging
        print(f"Email sending failed: {e}")
        return False

# Add this new function to your notifications.py file
    """
    Send email notifications when contacts are tagged in a ticket:
    1. Tagged contacts
    2. Person who tagged
    3. Ticket creator
    4. Assigned person
    """
    recipients = set()

    # Add tagged contacts
    for contact in tagged_contacts:
        if contact.email:
            recipients.add(contact.email)
    
    # Add person who tagged
    if tagged_by.email:
        recipients.add(tagged_by.email)
    
    # Add ticket creator
    if ticket.created_by and ticket.created_by.email:
        recipients.add(ticket.created_by.email)
    
    # Add assigned person
    if ticket.assigned_to and ticket.assigned_to.email:
        recipients.add(ticket.assigned_to.email)

    if not recipients:
        return False

    subject = f"[{ticket.company.name}] Contacts Tagged in Ticket: {ticket.title}"

    context = {
        'ticket': ticket,
        'company': ticket.company,
        'tagged_by': tagged_by,
        'tagged_contacts': tagged_contacts,
        'ticket_url': f"{settings.SITE_URL}/user_tickets/{ticket.id}/",
    }

    html_content = render_to_string('emails/contacts_tagged.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(recipients)
    )
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False