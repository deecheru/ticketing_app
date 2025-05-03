from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceFamily, ServiceType, ServiceCategory,Ticket
from .forms import *
from django.contrib.auth.decorators import login_required,user_passes_test
from accounts.models import User

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
            # Handle the case where the category ID is invalid
            pass
    try:
        admin_user = User.objects.get(username='deecheru')  # Ensure this matches your admin username
    except User.DoesNotExist:
        # Handle the case where the admin user doesn't exist
        # You might want to log an error or display a message
        admin_user = None
        print("Warning: Admin user not found. Tickets will not be automatically assigned.")
    if request.method == 'POST':
        form = TicketForm(request.POST,user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.company = request.user.company
            if admin_user:
                ticket.assigned_to = admin_user
            ticket.save()
            return redirect('view_ticket', pk=ticket.pk)  # Replace 'ticket_detail' with your ticket detail view name
    else:
        if initial_category:
            form = TicketForm(user=request.user, initial={'category': initial_category})
        else:
            form = TicketForm(user=request.user)
        #form = TicketForm(user=request.user)
    return render(request, 'tickets/create_ticket.html', {'form': form})
@login_required
def view_ticket(request, pk): #Example of detail view, replace with your actual detail view
    ticket = get_object_or_404(Ticket, pk=pk)
    return render(request, 'tickets/view_ticket.html', {'ticket': ticket})

@login_required
def view_open_tickets(request):

    if request.user.is_staff:
        open_tickets = Ticket.objects.exclude(status='CLOSED').order_by('-created_at')
        #closed_ticket_count = Ticket.objects.filter(status='CLOSED').order_by('-created_at')
        # Fetch all tickets
    else:
        user_company = request.user.company
        #tickets = Ticket.objects.filter(user=request.user)
        open_tickets = Ticket.objects.filter(company=user_company).exclude(status='CLOSED').order_by('-created_at')
        #closed_ticket_count = Ticket.objects.filter(company=user_company, status='CLOSED').order_by('-created_at')
    

    context = {
        'open_tickets': open_tickets,
    }
    return render(request, 'tickets/open_tickets.html', context)

@login_required
def view_closed_tickets(request):

    if request.user.is_staff:
        #open_tickets = Ticket.objects.exclude(status='CLOSED').order_by('-created_at')
        closed_tickets = Ticket.objects.filter(status='CLOSED').order_by('-created_at')
        # Fetch all tickets
    else:
        user_company = request.user.company
        #tickets = Ticket.objects.filter(user=request.user)
        #open_tickets = Ticket.objects.filter(company=user_company).exclude(status='CLOSED').order_by('-created_at')
        closed_tickets = Ticket.objects.filter(company=user_company, status='CLOSED').order_by('-created_at')
    

    context = {
        'closed_tickets': closed_tickets,
    }
    return render(request, 'tickets/closed_tickets.html', context)

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
