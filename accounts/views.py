# accounts/views.py
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import User, Profile, StaffCompanyAssignment
from django.contrib import messages
from .forms import LoginForm, UserUpdateForm, ProfileUpdateForm, CompanyCreationForm, UserCreationForm, MFAVerificationForm, ForgotPasswordForm, ResetPasswordForm
from django.contrib.auth.decorators import login_required, user_passes_test
from user_tickets.models import Ticket
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.forms import PasswordChangeForm
from django.core.cache import cache
from .utils import generate_verification_code, send_email_verification, generate_totp_secret, generate_totp_uri, generate_qr_code, verify_totp
import pyotp
import qrcode
import base64
from io import BytesIO
from django.contrib.auth.hashers import make_password
from django.db.models import Q

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password,backend='django.contrib.auth.backends.ModelBackend')
            if user is None:
                # Try email as username
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password, backend='django.contrib.auth.backends.ModelBackend')
                except User.DoesNotExist:
                    user = None

            if user is not None:
                if not user.profile.first_login_completed:
                    request.session['first_login_user_id'] = user.id
                    return redirect('first_login_mfa')
                elif user.profile.mfa_enabled:
                    request.session['mfa_user_id'] = user.id
                    return redirect('verify_mfa_login')
                else:
                    login(request, user)
                    return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username/email or password. Please try again.')
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = LoginForm()

    # Display any messages
    if messages.get_messages(request):
        for message in messages.get_messages(request):
            if message.tags == 'error':
                messages.error(request, message.message)
            else:
                messages.success(request, message.message)

    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard_view(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_superuser:  # Check if the user is an admin (superuser)
        open_ticket_count = Ticket.objects.exclude(status='CLOSED').count()
        closed_ticket_count = Ticket.objects.filter(status='CLOSED').count()
    elif request.user.is_staff:  # Check if the user is a staff member
        assigned_companies = StaffCompanyAssignment.objects.filter(staff_user=request.user).values_list('company', flat=True)
        open_ticket_count = Ticket.objects.filter(company__in=assigned_companies).exclude(status='CLOSED').count()
        closed_ticket_count = Ticket.objects.filter(company__in=assigned_companies, status='CLOSED').count()
    else:
        user_company = request.user.company
        open_ticket_count = Ticket.objects.filter(company=user_company).exclude(status='CLOSED').count()
        closed_ticket_count = Ticket.objects.filter(company=user_company, status='CLOSED').count()
    
    # Add any context data you want to pass to the template
    context = {
        'user': request.user,
        'open_ticket_count': open_ticket_count,
        'closed_ticket_count': closed_ticket_count,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

def logout_view(request):
    if request.user.is_authenticated:
        # Clear session data from cache
        session_key = f"user_session_{request.user.id}"
        cache.delete(session_key)
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
    # Initialize forms
    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=request.user.profile)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile_view')
        else:
            messages.error(request, 'Please correct the errors below in your profile.')
    
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

@login_required
def enable_mfa(request):
    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            profile = request.user.profile
            
            if verify_totp(profile.mfa_secret, verification_code):
                profile.mfa_enabled = True
                profile.mfa_verified = True
                profile.save()
                messages.success(request, 'Two-factor authentication has been enabled successfully!')
                return redirect('profile_view')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        # Generate new TOTP secret if not exists
        profile = request.user.profile
        if not profile.mfa_secret:
            profile.mfa_secret = generate_totp_secret()
            profile.save()
        
        # Generate QR code
        totp = pyotp.TOTP(profile.mfa_secret)
        provisioning_uri = totp.provisioning_uri(
            request.user.username,
            issuer_name="Ticketing_app"
        )
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        form = MFAVerificationForm()
        context = {
            'form': form,
            'qr_code': qr_code,
            'secret': profile.mfa_secret
        }
        return render(request, 'accounts/enable_mfa.html', context)

@login_required
def disable_mfa(request):
    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            profile = request.user.profile
            
            if verify_totp(profile.mfa_secret, verification_code):
                profile.mfa_enabled = False
                profile.mfa_verified = False
                profile.mfa_secret = None
                profile.save()
                messages.success(request, 'Two-factor authentication has been disabled.')
                return redirect('profile_view')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        form = MFAVerificationForm()
    
    return render(request, 'accounts/disable_mfa.html', {'form': form})

def verify_mfa_login(request):
    if 'mfa_user_id' not in request.session:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=request.session['mfa_user_id'])
    except User.DoesNotExist:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('login')

    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            
            if verify_totp(user.profile.mfa_secret, verification_code):
                # Set the backend attribute before login
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                del request.session['mfa_user_id']
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        form = MFAVerificationForm()
    
    return render(request, 'accounts/verify_mfa_login.html', {'form': form})

def first_login_mfa(request):
    if 'first_login_user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['first_login_user_id'])
    
    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            if verify_totp(user.profile.mfa_secret, verification_code):
                # Enable MFA and mark first login as completed
                user.profile.mfa_enabled = True
                user.profile.mfa_verified = True
                user.profile.first_login_completed = True
                user.profile.save()
                
                # Log the user in
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                del request.session['first_login_user_id']
                messages.success(request, 'Two-factor authentication has been set up successfully.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid verification code.')
    else:
        # Generate new secret if not exists
        if not user.profile.mfa_secret:
            secret = pyotp.random_base32()
            user.profile.mfa_secret = secret
            user.profile.save()
        
        # Generate QR code
        totp = pyotp.TOTP(user.profile.mfa_secret)
        provisioning_uri = totp.provisioning_uri(
            user.username,
            issuer_name="Ticketing_app"
        )
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        form = MFAVerificationForm()
    
    return render(request, 'accounts/first_login_mfa.html', {
        'form': form,
        'qr_code': qr_code,
        'secret': user.profile.mfa_secret
    })

def verify_totp(secret, code):
    """Verify a TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def regenerate_mfa(request):
    # Check if we're in the login process
    if 'mfa_user_id' in request.session:
        try:
            user = User.objects.get(id=request.session['mfa_user_id'])
        except User.DoesNotExist:
            messages.error(request, 'Session expired. Please login again.')
            return redirect('login')
    else:
        # If not in login process, require login
        if not request.user.is_authenticated:
            return redirect('login')
        user = request.user

    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            profile = user.profile
            
            if verify_totp(profile.mfa_secret, verification_code):
                # Enable MFA and mark as verified
                profile.mfa_enabled = True
                profile.mfa_verified = True
                profile.save()
                
                messages.success(request, 'New MFA code has been set up successfully.')
                
                # If in login process, redirect back to verification page
                if 'mfa_user_id' in request.session:
                    return redirect('verify_mfa_login')
                else:
                    return redirect('profile_view')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        # Generate new secret
        new_secret = pyotp.random_base32()
        profile = user.profile
        profile.mfa_secret = new_secret
        profile.mfa_enabled = False  # Disable MFA until verified
        profile.mfa_verified = False
        profile.save()
        
        # Generate QR code
        totp = pyotp.TOTP(new_secret)
        provisioning_uri = totp.provisioning_uri(
            user.username,
            issuer_name="Ticketing_app"
        )
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        form = MFAVerificationForm()
    
    return render(request, 'accounts/regenerate_mfa.html', {
        'form': form,
        'qr_code': qr_code,
        'secret': new_secret,
        'is_login': 'mfa_user_id' in request.session
    })

@login_required
def change_password(request):
    """View for changing user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile_view')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

def forgot_password(request):
    """View for handling forgot password requests"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate a unique token
                token = get_random_string(length=32)
                # Store token in user's profile
                user.profile.password_reset_token = token
                user.profile.password_reset_token_created = timezone.now()
                user.profile.save()
                
                # Send email with reset link
                reset_url = request.build_absolute_uri(f'/accounts/reset-password/{token}/')
                send_mail(
                    'Password Reset Request',
                    f'Click the following link to reset your password: {reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Password reset instructions have been sent to your email.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No user found with that email address.')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})

def reset_password(request, token):
    """View for resetting password with token"""
    try:
        profile = Profile.objects.get(password_reset_token=token)
        # Check if token is expired (24 hours)
        if timezone.now() - profile.password_reset_token_created > timedelta(hours=24):
            messages.error(request, 'Password reset link has expired.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                # Verify username matches the token
                entered_username = form.cleaned_data['username']
                if entered_username != profile.user.username:
                    messages.error(request, 'Invalid username. Please enter your correct username.')
                    return render(request, 'accounts/reset_password.html', {
                        'form': form,
                        'token': token
                    })
                
                # Update password
                user = profile.user
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                
                # Clear the reset token
                profile.password_reset_token = None
                profile.password_reset_token_created = None
                profile.save()
                
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('login')
        else:
            form = ResetPasswordForm()
        return render(request, 'accounts/reset_password.html', {
            'form': form,
            'token': token
        })
    except Profile.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('forgot_password')