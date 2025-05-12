from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceFamily, ServiceType, ServiceCategory,Ticket,TicketAttachment,TicketComment
from .forms import *
from django.contrib.auth.decorators import login_required,user_passes_test
from accounts.models import User
from django.contrib import messages
from .notifications import send_ticket_creation_notification, send_new_comment_notification,send_ticket_updated_notification   
import csv
from django.http import HttpResponse
from django.utils import timezone

def is_staff_check(user):
    return user.is_staff

@login_required
def select_service(request):
    user_company = request.user.company
    service_families = ServiceFamily.objects.filter(company=user_company)
    service_types = ServiceType.objects.filter(family__company=user_company)
    service_categories = ServiceCategory.objects.filter(service_type__family__company=user_company)


    context = {
        'service_families': service_families,
        'service_types': service_types,
        'service_categories': service_categories,
    }
    return render(request, 'tickets/select_service.html', context)

@login_required
def create_ticket(request):
    initial_category_id = request.GET.get('category')
    initial_category = None
    if initial_category_id:
        try:
            initial_category = ServiceCategory.objects.get(id=initial_category_id)
        except ServiceCategory.DoesNotExist:
            pass
    
    try:
        admin_user = User.objects.get(username='deecheru')  # Ensure this matches your admin username
    except User.DoesNotExist:
        admin_user = None
        print("Warning: Admin user not found. Tickets will not be automatically assigned.")
    
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        comment_form = TicketCommentForm(request.POST)
        files = request.FILES.getlist('attachments')
        
        if form.is_valid() and comment_form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.company = request.user.company
            if admin_user:
                ticket.assigned_to = admin_user
            ticket.save()
            form.save_m2m()

            comment_text = comment_form.cleaned_data.get('text')
            if comment_text:
                TicketComment.objects.create(
                    ticket=ticket,
                    text=comment_text,
                    created_by=request.user
                )

            
            # Process file attachments
            for f in files:
                attachment = TicketAttachment(
                    ticket=ticket,
                    file=f,
                    filename=f.name,
                    uploaded_by=request.user
                )
                attachment.save()
            
            messages.success(request, 'Ticket created successfully.')
            return redirect('view_ticket', pk=ticket.pk)
    else:
        if initial_category:
            form = TicketForm(user=request.user, initial={'category': initial_category})
        else:
            form = TicketForm(user=request.user)
        comment_form = TicketCommentForm()
    
    return render(request, 'tickets/create_ticket.html', {'form': form,  'comment_form': comment_form,})

@login_required
def view_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    comment_form = TicketCommentForm()

    if request.method == 'POST':
        comment_form = TicketCommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.ticket = ticket
            new_comment.created_by = request.user
            new_comment.save()
            send_new_comment_notification(new_comment) 
            messages.success(request, 'Comment added successfully.')
            return redirect('view_ticket', pk=pk)

    # Get the referrer URL
    referrer = request.META.get('HTTP_REFERER', '')
    back_url = 'dashboard'  # Default fallback
    
    # Determine which page the user came from
    if 'open-tickets' in referrer:
        back_url = 'open_tickets'
    elif 'closed-tickets' in referrer:
        back_url = 'closed_tickets'

    context = {
        'ticket': ticket,
        'comment_form': comment_form,
        'back_url': back_url,
    }
    return render(request, 'tickets/view_ticket.html', context)

def generate_ticket_csv(tickets):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tickets.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ticket ID', 'Title', 'Status', 'Priority', 'Created By', 'Created At', 'Assigned To', 'Category'])
    
    for ticket in tickets:
        writer.writerow([
            ticket.id,
            ticket.title,
            ticket.get_status_display(),
            ticket.get_priority_display(),
            ticket.created_by.get_full_name() if ticket.created_by else 'Unknown',
            ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            ticket.assigned_to.get_full_name() if ticket.assigned_to else 'Unassigned',
            ticket.category.name if ticket.category else 'Uncategorized'
        ])
    
    return response

@login_required
def view_open_tickets(request):
    user = request.user
    company = user.company
    
    # Get all open tickets for the user's company
    open_tickets = Ticket.objects.filter(
        company=company,
        status__in=['OPEN', 'IN_PROGRESS', 'PENDING']
    ).order_by('-created_at')
    
    # Handle CSV download
    if request.GET.get('download') == 'csv':
        return generate_ticket_csv(open_tickets)
    
    context = {
        'open_tickets': open_tickets,
        'user': user
    }
    return render(request, 'tickets/open_tickets.html', context)

@login_required
def view_closed_tickets(request):
    user = request.user
    company = user.company
    
    # Get all closed tickets for the user's company
    closed_tickets = Ticket.objects.filter(
        company=company,
        status__in=['RESOLVED', 'CLOSED']
    ).order_by('-created_at')
    
    # Handle CSV download
    if request.GET.get('download') == 'csv':
        return generate_ticket_csv(closed_tickets)
    
    context = {
        'closed_tickets': closed_tickets,
        'user': user
    }
    return render(request, 'tickets/closed_tickets.html', context)

@login_required
def edit_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Check if the current user has permission to edit the ticket
    if not (request.user == ticket.created_by or request.user.is_staff):
        messages.error(request, "You do not have permission to edit this ticket.")
        return redirect('view_ticket', pk=pk)

    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES, instance=ticket, user=request.user)
        files = request.FILES.getlist('attachments')
        if form.is_valid():
            old_ticket = Ticket.objects.get(pk=pk)
            updated_ticket = form.save(commit=False)
            updated_ticket.save()
            form.save_m2m()

            # Handle attachments
            for f in files:
                attachment = TicketAttachment(ticket=updated_ticket, file=f, filename=f.name, uploaded_by=request.user)
                attachment.save()

            # Detect changes for notification
            changes = {}
            if updated_ticket.title != old_ticket.title:
                changes['Title'] = (old_ticket.title, updated_ticket.title)
            if updated_ticket.description != old_ticket.description:
                changes['Description'] = (old_ticket.description, updated_ticket.description)
            if updated_ticket.status != old_ticket.status:
                changes['Status'] = (old_ticket.get_status_display(), updated_ticket.get_status_display())
            if updated_ticket.priority != old_ticket.priority:
                changes['Priority'] = (old_ticket.get_priority_display(), updated_ticket.get_priority_display())
            if updated_ticket.category != old_ticket.category:
                changes['Category'] = (
                    old_ticket.category.name if old_ticket.category else "None", 
                    updated_ticket.category.name if updated_ticket.category else "None"
                )
            if updated_ticket.impact != old_ticket.impact:
                changes['Impact'] = (old_ticket.get_impact_display(), updated_ticket.get_impact_display())
            if updated_ticket.assigned_to != old_ticket.assigned_to:
                changes['Assigned To'] = (
                    old_ticket.assigned_to.username if old_ticket.assigned_to else "None", 
                    updated_ticket.assigned_to.username if updated_ticket.assigned_to else "None"
                )

            # Handle contacts changes - ensure we always have two values for template unpacking
            old_contacts = set(old_ticket.contacts.values_list('id', flat=True))
            new_contacts = set(updated_ticket.contacts.values_list('id', flat=True))
            added_contacts = new_contacts - old_contacts
            removed_contacts = old_contacts - new_contacts
            
            if added_contacts or removed_contacts:
                added_names = [User.objects.get(id=user_id).username for user_id in added_contacts]
                removed_names = [User.objects.get(id=user_id).username for user_id in removed_contacts]
                
                # Properly format as a tuple with two values
                old_value = "None" if not removed_names else f"Included: {', '.join(removed_names)}"
                new_value = "None" if not added_names else f"Added: {', '.join(added_names)}"
                changes['Contacts'] = (old_value, new_value)

            # Only send notification if there were changes or new files
            if changes or files:
                send_ticket_updated_notification(updated_ticket, request.user, changes, files)

            messages.success(request, 'Ticket updated successfully.')
            return redirect('view_ticket', pk=updated_ticket.pk)
        else:
            messages.error(request, 'There was an error updating the ticket.')
    else:
        form = TicketForm(instance=ticket, user=request.user)
    return render(request, 'tickets/edit_ticket.html', {'form': form, 'ticket': ticket})


#********************************#
@login_required
@user_passes_test(is_staff_check)
def add_service_family(request):
    if request.method == 'POST':
        form = ServiceFamilyCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Replace with your success URL
    else:
        form = ServiceFamilyCreationForm()

    return render(request, 'tickets/add_service_family.html', {'form': form})

@login_required
@user_passes_test(is_staff_check)
def add_service_type(request):
    if request.method == 'POST':
        form = ServiceTypeCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Replace with your success URL
    else:
        form = ServiceTypeCreationForm()
    return render(request, 'tickets/add_service_type.html', {'form': form})

@login_required
@user_passes_test(is_staff_check)
def add_service_category(request):
    if request.method == 'POST':
        form = ServiceCategoryCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Replace with your success URL
    else:
        form = ServiceCategoryCreationForm()
    return render(request, 'tickets/add_service_category.html', {'form': form})
