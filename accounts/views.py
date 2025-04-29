# accounts/views.py
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from .forms import LoginForm

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

def dashboard_view(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')
        
    # Add any context data you want to pass to the template
    context = {
        'user': request.user,
        # Add other dashboard data like ticket counts, recent tickets, etc.
    }
    
    return render(request, 'dashboard/dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')