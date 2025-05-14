from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('select-service/', views.select_service, name='select_service'),
    path('create-ticket/',views.create_ticket, name = 'create_ticket'),
    path('<int:pk>/', views.view_ticket, name='view_ticket'),
    path('open-tickets/', views.view_open_tickets, name='open_tickets'),
    path('closed-tickets/', views.view_closed_tickets, name='closed_tickets'),
    path('add-service-family/', views.add_service_family, name='add_service_family'),
    path('add-service-type/', views.add_service_type, name='add_service_type'),
    path('add-service-category/', views.add_service_category, name='add_service_category'),
    path('user_tickets/<int:pk>/edit/', views.edit_ticket, name='edit_ticket'),
    path('api/service-types/', views.get_service_types, name='get_service_types'),
    path('api/service-categories/', views.get_service_categories, name='get_service_categories'),
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/companies/', views.admin_manage_companies, name='admin_manage_companies'),
    path('admin/users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin/tickets/', views.admin_manage_tickets, name='admin_manage_tickets'),
    path('admin/staff-companies/', views.admin_manage_staff_companies, name='admin_manage_staff_companies'),
    path('admin/staff-companies/<int:assignment_id>/remove/', views.remove_staff_company, name='remove_staff_company'),
    path('api/service-types/', views.get_service_types, name='api_service_types'),
    path('api/service-categories/', views.get_service_categories, name='api_service_categories'),
]

