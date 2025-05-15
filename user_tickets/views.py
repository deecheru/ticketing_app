from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceFamily, ServiceType, ServiceCategory, Ticket, TicketAttachment, TicketComment
from accounts.models import User, Company, Profile, StaffCompanyAssignment
from .forms import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .notifications import send_ticket_creation_notification, send_new_comment_notification, send_ticket_updated_notification   
import csv
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count
from django.db.models import Q
from django.db.utils import IntegrityError
from django.db import models

def is_staff_check(user):
    return user.is_staff

def is_company_agent_check(user):
    return user.is_company_agent

@login_required
def select_service(request):
    user_company = request.user.company
    service_families = ServiceFamily.objects.filter(company=user_company)
    service_types = ServiceType.objects.filter(family__company=user_company)
    service_categories = ServiceCategory.objects.filter(service_type__family__company=user_company)

    # Add this part to handle form submission from select_service page
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        if category_id:
            # Redirect to create_ticket with the category ID
            return redirect(f'/tickets/create-ticket/?category_id={category_id}')
        else:
            messages.warning(request, 'Please select a category first.')

    context = {
        'service_families': service_families,
        'service_types': service_types,
        'service_categories': service_categories,
    }
    return render(request, 'tickets/select_service.html', context)

@login_required
def create_ticket(request):
    user = request.user
    initial_category_id = request.GET.get('category_id')
    initial_category = None
    initial_service_type = None
    initial_service_family = None
    
    if initial_category_id:
        try:
            # Get the initial category and its parent objects
            initial_category = ServiceCategory.objects.filter(
                service_type__family__company=user.company
            ).get(id=initial_category_id)
            
            # Get the parent service type
            initial_service_type = initial_category.service_type
            
            # Get the parent service family
            initial_service_family = initial_service_type.family
        except ServiceCategory.DoesNotExist:
            messages.warning(request, 'Selected category not found.')
    
    # Get admin user for assignment
    admin_user = None
    try:
        admin_user = User.objects.get(username='deecheru')
    except User.DoesNotExist:
        print("Warning: Admin user not found")
    
    if request.method == 'POST':
        form = TicketForm(request.POST, user=user)
        comment_form = TicketCommentForm(request.POST)
        
        if form.is_valid() and comment_form.is_valid():
            try:
                ticket = form.save(commit=False)
                ticket.created_by = user
                ticket.company = user.company  # Ensure company is set from the user
                ticket.status = 'OPEN'  # Explicitly set status to OPEN
                if admin_user:
                    ticket.assigned_to = admin_user
                ticket.save()
                form.save_m2m()
                
                # Create initial comment if provided
                if comment_form.cleaned_data['text']:
                    TicketComment.objects.create(
                        ticket=ticket,
                        text=comment_form.cleaned_data['text'],
                        created_by=user
                    )
                
                # Handle file attachments
                files = request.FILES.getlist('attachments')
                for file in files:
                    TicketAttachment.objects.create(
                        ticket=ticket,
                        file=file,
                        filename=file.name,
                        file_type=file.content_type,
                        size=file.size,
                        uploaded_by=user
                    )
                
                messages.success(request, 'Ticket created successfully!')
                return redirect('view_ticket', pk=ticket.id)
            except Exception as e:
                messages.error(request, f'Error creating ticket: {str(e)}')
        else:
            if form.errors:
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
            
                # Send errors to messages
                for error_message in error_messages:
                    messages.error(request, error_message)

                messages.error(request, 'Please correct the errors below.')
    else:
        # Initialize form with preselected values
        initial_data = {}
        
        # If we have a valid initial category, set it and its parents in the initial data
        if initial_category:
            initial_data['category'] = initial_category.id
            
            if initial_service_type:
                initial_data['service_type'] = initial_service_type.id
                
                if initial_service_family:
                    initial_data['service_family'] = initial_service_family.id

        form = TicketForm(user=user, initial=initial_data)
        comment_form = TicketCommentForm()
    
    # Pass all necessary data to the template
    return render(request, 'tickets/create_ticket.html', {
        'form': form,
        'comment_form': comment_form,
        'initial_category': initial_category,
        'initial_service_type': initial_service_type,
        'initial_service_family': initial_service_family
    })

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
    
    # For admin users, show all open tickets
    if user.is_superuser:
        open_tickets = Ticket.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS', 'RESOLVED']
        )
    # For company agents, show tickets from assigned companies
    elif user.is_company_agent:
        assigned_companies = user.assigned_companies.values_list('company', flat=True)
        open_tickets = Ticket.objects.filter(
            company__in=assigned_companies,
            status__in=['OPEN', 'IN_PROGRESS', 'RESOLVED']
        )
    else:
        # For regular users, show all tickets from their company
        company = user.company
        open_tickets = Ticket.objects.filter(
            company=company,
            status__in=['OPEN', 'IN_PROGRESS', 'RESOLVED']              
        )
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        open_tickets = open_tickets.filter(
            # Search across multiple fields
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(id__icontains=search_query) |
            models.Q(status__icontains=search_query) |
            models.Q(priority__icontains=search_query) |
            models.Q(created_by__username__icontains=search_query) |
            models.Q(created_by__first_name__icontains=search_query) |
            models.Q(created_by__last_name__icontains=search_query)
        )
    
    # Apply ordering after search
    open_tickets = open_tickets.order_by('-created_at')
    
    # Handle CSV download
    if request.GET.get('download') == 'csv':
        return generate_ticket_csv(open_tickets)
    
    context = {
        'open_tickets': open_tickets,
        'user': user,
        'is_admin': user.is_superuser,
        'is_company_agent': user.is_company_agent,
        'search_query': search_query,  # Pass search query to template for display
    }
    return render(request, 'tickets/open_tickets.html', context)

@login_required
def view_closed_tickets(request):
    user = request.user
    
    # For admin users, show all closed tickets
    if user.is_superuser:
        closed_tickets = Ticket.objects.filter(status='CLOSED').order_by('-created_at')
    # For company agents, show tickets from assigned companies
    elif user.is_company_agent:
        assigned_companies = user.assigned_companies.values_list('company', flat=True)
        closed_tickets = Ticket.objects.filter(
            company__in=assigned_companies,
            status='CLOSED'
        )
    else:
        # For regular users, show closed tickets from their company
        company = user.company
        closed_tickets = Ticket.objects.filter(
            company=company,
            status='CLOSED'              
        )
    
    # Handle search functionality - case-insensitive search
    search_query = request.GET.get('search', '')
    if search_query:
        closed_tickets = closed_tickets.filter(
            # Search across multiple fields using icontains for case-insensitive matching
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(id__icontains=search_query) |
            models.Q(status__icontains=search_query) |
            models.Q(priority__icontains=search_query) |
            models.Q(created_by__username__icontains=search_query) |
            models.Q(created_by__first_name__icontains=search_query) |
            models.Q(created_by__last_name__icontains=search_query)
        )
    
    # Apply ordering after search
    closed_tickets = closed_tickets.order_by('-created_at')
    
    # Handle CSV download
    if request.GET.get('download') == 'csv':
        return generate_ticket_csv(closed_tickets)
    
    context = {
        'closed_tickets': closed_tickets,
        'user': user,
        'is_admin': user.is_superuser,
        'is_company_agent': user.is_company_agent,
        'search_query': search_query,  # Pass search query to template for display
    }
    return render(request, 'tickets/closed_tickets.html', context)

@login_required
def edit_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user

    # Check if the current user has permission to edit the ticket
    can_edit = (
        user.is_superuser or  # Admin can edit any ticket
        user == ticket.created_by or  # Creator can edit their ticket
        (user.is_company_agent and user.assigned_companies.filter(company=ticket.company).exists())  # Company agent can edit assigned company tickets
    )

    if not can_edit:
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

            # Handle contacts changes
            old_contacts = set(old_ticket.contacts.values_list('id', flat=True))
            new_contacts = set(updated_ticket.contacts.values_list('id', flat=True))
            added_contacts = new_contacts - old_contacts
            removed_contacts = old_contacts - new_contacts
            
            if added_contacts or removed_contacts:
                added_names = [User.objects.get(id=user_id).username for user_id in added_contacts]
                removed_names = [User.objects.get(id=user_id).username for user_id in removed_contacts]
                changes['Contacts'] = (
                    "None" if not removed_names else f"Included: {', '.join(removed_names)}",
                    "None" if not added_names else f"Added: {', '.join(added_names)}"
                )

            # Only send notification if there were changes or new files
            if changes or files:
                send_ticket_updated_notification(updated_ticket, request.user, changes, files)

            messages.success(request, 'Ticket updated successfully.')
            return redirect('view_ticket', pk=updated_ticket.pk)
        else:
            messages.error(request, 'There was an error updating the ticket.')
            print(form.errors)
    else:
        form = TicketForm(instance=ticket, user=request.user)
    
    context = {
        'form': form,
        'ticket': ticket,
        'is_company_agent': user.is_company_agent
    }
    return render(request, 'tickets/edit_ticket.html', context)


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

@login_required
@user_passes_test(is_staff_check)
def admin_dashboard(request):
    # Get statistics
    total_tickets = Ticket.objects.count()
    open_tickets = Ticket.objects.filter(status__in=['OPEN', 'IN_PROGRESS', 'PENDING']).count()
    closed_tickets = Ticket.objects.filter(status__in=['RESOLVED', 'CLOSED']).count()
    total_companies = Company.objects.count()
    total_users = User.objects.count()
    
    # Get recent tickets
    recent_tickets = Ticket.objects.all().order_by('-created_at')[:10]
    
    # Get company-wise ticket distribution
    company_stats = Company.objects.annotate(
        ticket_count=Count('company_tickets')
    ).order_by('-ticket_count')[:5]
    
    # Get status-wise ticket distribution
    status_stats = Ticket.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    context = {
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'closed_tickets': closed_tickets,
        'total_companies': total_companies,
        'total_users': total_users,
        'recent_tickets': recent_tickets,
        'company_stats': company_stats,
        'status_stats': status_stats,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_staff_check)
def admin_manage_companies(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        company_id = request.POST.get('company_id')
        
        if action == 'delete' and company_id:
            company = get_object_or_404(Company, id=company_id)
            company.delete()
            messages.success(request, f'Company {company.name} has been deleted.')
        else:
            name = request.POST.get('name')
            # Generate slug from company name
            slug = name.lower().replace(' ', '-')
            
            if company_id:  # Edit existing company
                company = get_object_or_404(Company, id=company_id)
                company.name = name
                company.slug = slug
                company.save()
                messages.success(request, f'Company {company.name} has been updated.')
            else:  # Create new company
                try:
                    Company.objects.create(name=name, slug=slug)
                    messages.success(request, f'New company {name} has been created.')
                except IntegrityError:
                    # If slug already exists, append a number
                    base_slug = slug
                    counter = 1
                    while True:
                        try:
                            Company.objects.create(name=name, slug=f"{base_slug}-{counter}")
                            messages.success(request, f'New company {name} has been created.')
                            break
                        except IntegrityError:
                            counter += 1
        
        return redirect('admin_manage_companies')
    
    # GET request - display companies with their stats
    companies = Company.objects.annotate(
        total_tickets=Count('company_tickets', distinct=True),
        open_tickets=Count(
            'company_tickets',
            filter=Q(company_tickets__status__in=['OPEN', 'IN_PROGRESS', 'PENDING']),
            distinct=True
        ),
        total_users=Count('users', distinct=True)
    ).order_by('name')
    
    return render(request, 'admin/manage_companies.html', {'companies': companies})

@login_required
@user_passes_test(is_staff_check)
def admin_manage_users(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'delete' and user_id:
            user = get_object_or_404(User, id=user_id)
            username = user.username
            user.delete()
            messages.success(request, f'User {username} has been deleted.')
        else:
            username = request.POST.get('username')
            email = request.POST.get('email')
            company_id = request.POST.get('company')
            is_staff = request.POST.get('is_staff') == 'on'
            is_active = request.POST.get('is_active') == 'on'
            
            try:
                company = Company.objects.get(id=company_id)
                
                if user_id:  # Edit existing user
                    user = get_object_or_404(User, id=user_id)
                    user.username = username
                    user.email = email
                    user.is_staff = is_staff
                    user.is_active = is_active
                    user.save()
                    
                    # Update profile
                    user.profile.company = company
                    user.profile.save()
                    
                    messages.success(request, f'User {username} has been updated.')
                else:  # Create new user
                    password = request.POST.get('password')
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        is_staff=is_staff,
                        is_active=True
                    )
                    user.profile.company = company
                    user.profile.save()
                    messages.success(request, f'New user {username} has been created.')
            except Company.DoesNotExist:
                messages.error(request, 'Invalid company selected.')
        
        return redirect('admin_manage_users')
    
    # GET request - display users with their companies
    users = User.objects.select_related('profile').all().order_by('username')
    companies = Company.objects.all().order_by('name')
    
    return render(request, 'admin/manage_users.html', {
        'users': users,
        'companies': companies
    })

@login_required
@user_passes_test(is_staff_check)
def admin_manage_tickets(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        ticket_id = request.POST.get('ticket_id')
        
        if action == 'delete' and ticket_id:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            ticket_title = ticket.title
            ticket.delete()
            messages.success(request, f'Ticket #{ticket_id} - {ticket_title} has been deleted.')
        else:
            title = request.POST.get('title')
            status = request.POST.get('status')
            priority = request.POST.get('priority')
            company_id = request.POST.get('company')
            
            try:
                company = Company.objects.get(id=company_id)
                
                if ticket_id:  # Edit existing ticket
                    ticket = get_object_or_404(Ticket, id=ticket_id)
                    ticket.title = title
                    ticket.status = status
                    ticket.priority = priority
                    ticket.company = company
                    ticket.save()
                    messages.success(request, f'Ticket #{ticket_id} has been updated.')
            except Company.DoesNotExist:
                messages.error(request, 'Invalid company selected.')
        
        return redirect('admin_manage_tickets')
    
    # GET request - display tickets with filters
    tickets = Ticket.objects.select_related('company', 'created_by').all()
    
    # Apply filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    company = request.GET.get('company')
    search = request.GET.get('search')
    
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    if company:
        tickets = tickets.filter(company_id=company)
    if search:
        tickets = tickets.filter(title__icontains=search)
    
    # Get choices for filters
    status_choices = Ticket.STATUS_CHOICES
    priority_choices = Ticket.PRIORITY
    companies = Company.objects.all().order_by('name')
    
    return render(request, 'admin/manage_tickets.html', {
        'tickets': tickets,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'companies': companies
    })

@login_required
@user_passes_test(is_staff_check)
def admin_manage_staff_companies(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        company_id = request.POST.get('company')
        
        if user_id and company_id:
            user = get_object_or_404(User, id=user_id)
            company = get_object_or_404(Company, id=company_id)
            
            # Check if assignment already exists
            if not StaffCompanyAssignment.objects.filter(user=user, company=company).exists():
                StaffCompanyAssignment.objects.create(
                    user=user,
                    company=company,
                    assigned_by=request.user
                )
                messages.success(request, f'Company {company.name} has been assigned to {user.get_full_name() or user.username}.')
            else:
                messages.warning(request, 'This company is already assigned to the selected user.')
    
    # Get all users and companies
    users = User.objects.filter(is_superuser=False)
    companies = Company.objects.all().order_by('name')
    assignments = StaffCompanyAssignment.objects.all().order_by('-assigned_at')
    
    context = {
        'users': users,
        'companies': companies,
        'assignments': assignments
    }
    return render(request, 'admin/manage_staff_companies.html', context)

@login_required
@user_passes_test(is_staff_check)
def remove_staff_company(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(StaffCompanyAssignment, id=assignment_id)
        user = assignment.user
        company = assignment.company
        assignment.delete()
        messages.success(request, f'Company {company.name} has been removed from {user.get_full_name() or user.username}.')
    return redirect('admin_manage_staff_companies')

@login_required
def get_service_types(request):
    family_id = request.GET.get('family_id')
    if not family_id:
        return JsonResponse([], safe=False)
    
    service_types = ServiceType.objects.filter(
        family_id=family_id,
        family__company=request.user.company
    ).values('id', 'name')
    
    return JsonResponse(list(service_types), safe=False)

def get_service_categories(request):
    type_id = request.GET.get('type_id')
    if not type_id:
        return JsonResponse([], safe=False)
    
    categories = ServiceCategory.objects.filter(
        service_type_id=type_id,
        service_type__family__company=request.user.company
    ).values('id', 'name')
    
    return JsonResponse(list(categories), safe=False)
