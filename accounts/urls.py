# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_update, name='profile_update'),
    path('add-user/',views.add_user, name = 'add_user'),
    path('add-company/',views.add_company, name = 'add_company'),
]