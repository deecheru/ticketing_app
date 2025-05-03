from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ServiceFamily)
admin.site.register(ServiceType)
admin.site.register(ServiceCategory)
admin.site.register(Ticket)