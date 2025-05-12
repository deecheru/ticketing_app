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
     path('user_tickets/<int:pk>/edit/', views.edit_ticket, name='edit_ticket')
]

