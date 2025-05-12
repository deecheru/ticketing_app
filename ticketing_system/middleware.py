from django.contrib.auth import logout
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
import json
from datetime import timedelta

class SessionManagementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get or create user session data
            session_key = f"user_session_{request.user.id}"
            session_data = cache.get(session_key)
            current_time = timezone.now()
            
            if not session_data:
                # Initialize new session data
                session_data = {
                    'user_id': request.user.id,
                    'username': request.user.username,
                    'is_admin': request.user.is_staff,
                    'last_activity': current_time.isoformat(),
                    'ip_address': self.get_client_ip(request),
                    'session_id': request.session.session_key,
                }
                cache.set(session_key, json.dumps(session_data), timeout=3600)  # 1 hour timeout
            else:
                # Update existing session data
                session_data = json.loads(session_data)
                last_activity = timezone.datetime.fromisoformat(session_data['last_activity'])
                
                # Check for session timeout
                if current_time - last_activity > timedelta(hours=1):
                    logout(request)
                    messages.error(request, "Your session has expired due to inactivity.")
                    return redirect('login')
                
                # Update last activity
                session_data['last_activity'] = current_time.isoformat()
                cache.set(session_key, json.dumps(session_data), timeout=3600)

            # Check for session conflicts
            if self.has_session_conflict(request, session_data):
                logout(request)
                messages.error(request, "Your session has been terminated due to login from another device.")
                return redirect('login')

            # Check admin access
            if request.path.startswith('/admin/') and not request.user.is_staff:
                messages.error(request, "You don't have permission to access the admin panel.")
                return redirect('dashboard')

            # Update session expiry
            request.session.set_expiry(3600)  # 1 hour

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def has_session_conflict(self, request, session_data):
        # Check if the current IP is different from the stored IP
        current_ip = self.get_client_ip(request)
        stored_ip = session_data.get('ip_address')
        current_session_id = request.session.session_key
        stored_session_id = session_data.get('session_id')
        
        if stored_ip and current_ip != stored_ip:
            # Allow admin users to have multiple sessions
            if not request.user.is_staff:
                return True
        
        # Check if session ID matches
        if stored_session_id and current_session_id != stored_session_id:
            if not request.user.is_staff:
                return True
                
        return False 