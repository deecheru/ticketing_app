from django import forms
from .models import Ticket,ServiceCategory,ServiceFamily,ServiceType,TicketComment

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'impact', 'priority', 'category','contacts']
        widgets = {'contacts': forms.SelectMultiple(attrs={'class': 'form-select', 'multiple': True}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
        if user and user.company:
            company = user.company
            
            # This traverses the relationships: Category -> ServiceType -> ServiceFamily -> Company
            self.fields['category'].queryset = ServiceCategory.objects.filter(
                service_type__family__company=company)
            self.fields['contacts'].queryset = user.company.users.exclude(id=user.id)
class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'rows': 3, 'placeholder': 'Add an initial comment (optional)'}),
        }
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
  