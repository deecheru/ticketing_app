# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    #path('register/', views.register, name='register'),
    
    # Password Reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # MFA URLs
    path('verify-mfa-login/', views.verify_mfa_login, name='verify_mfa_login'),
    path('regenerate-mfa/', views.regenerate_mfa, name='regenerate_mfa'),
    path('first-login-mfa/', views.first_login_mfa, name='first_login_mfa'),
    path('enable-mfa/', views.enable_mfa, name='enable_mfa'),
    path('disable-mfa/', views.disable_mfa, name='disable_mfa'),
    
    # Dashboard URL
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Admin URLs
    path('add-user/', views.add_user, name='add_user'),
    path('add-company/', views.add_company, name='add_company'),
]