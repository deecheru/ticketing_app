# accounts/views.py
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.db import transaction
from .models import User, Profile
from django.contrib import messages
from .forms import LoginForm,UserUpdateForm, ProfileUpdateForm, CompanyCreationForm,UserCreationForm
from django.contrib.auth.decorators import login_required,user_passes_test
from user_tickets.models import Ticket

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard_view(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_superuser:  # Check if the user is an admin (superuser)
        open_ticket_count = Ticket.objects.exclude(status='CLOSED').count()
        closed_ticket_count = Ticket.objects.filter(status='CLOSED').count()
        #all_open_tickets = Ticket.objects.exclude(status='CLOSED').order_by('-created_at') # Fetch all open tickets for admin
    else:
        user_company = request.user.company
        open_ticket_count = Ticket.objects.filter(company=user_company).exclude(status='CLOSED').count()
        closed_ticket_count = Ticket.objects.filter(company=user_company, status='CLOSED').count()
        #all_open_tickets = Ticket.objects.filter(company=user_company).exclude(status='CLOSED').order_by('-created_at')  
    # Add any context data you want to pass to the template
    context = {
        'user': request.user,
        'open_ticket_count': open_ticket_count,
        'closed_ticket_count': closed_ticket_count,
        # Add other dashboard data like ticket counts, recent tickets, etc.
    }
    
    return render(request, 'dashboard/dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    """Display the user's profile"""
    # The profile is available via request.user.profile
    return render(request, 'accounts/profile.html')


@login_required
@transaction.atomic  # Ensures both forms are saved or none
def profile_update(request):
    """Update the user's profile"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile_view')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile_update.html', context)

#*************************#
def is_staff_check(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_check)
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard') 
    else:
        form = UserCreationForm()
    return render(request, 'accounts/add_user.html', {'form': form})

@login_required
@user_passes_test(is_staff_check)
def add_company(request):
    if request.method == 'POST':
        form = CompanyCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CompanyCreationForm()
    return render(request, 'accounts/add_company.html', {'form': form})