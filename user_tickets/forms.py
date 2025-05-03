from django import forms
from .models import Ticket,ServiceCategory,ServiceFamily,ServiceType

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'impact', 'priority', 'category']
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
        if user and user.company:
            company = user.company
            
            # This traverses the relationships: Category -> ServiceType -> ServiceFamily -> Company
            self.fields['category'].queryset = ServiceCategory.objects.filter(
                service_type__family__company=company
            )
#*********************************************#

class ServiceFamilyCreationForm(forms.ModelForm):
    class Meta:
        model = ServiceFamily
        fields = ('name', 'description', 'company')
        # The company will likely be pre-filled or selected by the admin

class ServiceTypeCreationForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ('name', 'description', 'family')
        # The family will be selected from existing ServiceFamilies

class ServiceCategoryCreationForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ('name', 'description', 'service_type')
        # The service_type will be selected from existing ServiceTypes

class TicketCreationFormForAdmin(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'status', 'impact', 'priority', 'company', 'category', 'created_by', 'assigned_to')
  