from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
     path('', accounts_views.login_view, name='login'),
    path('accounts/', include('accounts.urls')),
    path('user_tickets/', include('user_tickets.urls')),
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)