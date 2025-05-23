from django import forms
from .models import Ticket,ServiceCategory,ServiceFamily,ServiceType,TicketComment,User

class TicketForm(forms.ModelForm):
    service_family = forms.ModelChoiceField(
        queryset=ServiceFamily.objects.none(),
        required=True,
        label='Service Family'
    )
    service_type = forms.ModelChoiceField(
        queryset=ServiceType.objects.none(),
        required=True,
        label='Service Type'
    )
    
    

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'impact', 'priority', 'category', 'contacts', 'status']
        
        widgets = {
            'contacts': forms.SelectMultiple(attrs={'class': 'form-select', 'multiple': True}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'required': False}),
            'impact': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}), 
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
        if user:
            # Get the company based on user type
            if user.is_company_agent:
                # For company agents, get all assigned companies
                assigned_companies = user.assigned_companies.values_list('company', flat=True)
                if assigned_companies:
                    # Set up service family queryset for all assigned companies
                    self.fields['service_family'].queryset = ServiceFamily.objects.filter(company__in=assigned_companies)
                    
                    # Set up service type queryset based on selected family
                    if 'service_family' in self.data:
                        try:
                            family_id = int(self.data.get('service_family'))
                            self.fields['service_type'].queryset = ServiceType.objects.filter(family_id=family_id)
                        except (ValueError, TypeError):
                            pass
                    
                    # Filter categories to show those from assigned companies
                    self.fields['category'].queryset = ServiceCategory.objects.filter(
                        service_type__family__company__in=assigned_companies
                    ).order_by('name')
                    
                    # Filter contacts to show users from assigned companies
                    self.fields['contacts'].queryset = User.objects.filter(
                        company__in=assigned_companies
                    ).exclude(id=user.id)
            else:
                # For regular users, use their company
                company = user.company
                if company:
                    # Set up service family queryset
                    self.fields['service_family'].queryset = ServiceFamily.objects.filter(company=company)
                    
                    # Set up service type queryset based on selected family
                    if 'service_family' in self.data:
                        try:
                            family_id = int(self.data.get('service_family'))
                            self.fields['service_type'].queryset = ServiceType.objects.filter(family_id=family_id)
                        except (ValueError, TypeError):
                            pass
                    
                    # Filter categories to only show those from the user's company
                    self.fields['category'].queryset = ServiceCategory.objects.filter(
                        service_type__family__company=company
                    ).order_by('name')
                    
                    # Filter contacts to only show users from the same company
                    self.fields['contacts'].queryset = company.users.exclude(id=user.id)
            
            self.fields['contacts'].help_text = 'Hold Ctrl (Windows) or Command (Mac) to select or deselect multiple contacts.'
            
            # If initial category is provided, set up the related querysets
            if 'initial' in kwargs and 'category' in kwargs['initial']:
                category_id = kwargs['initial']['category']
                try:
                    category_obj = ServiceCategory.objects.get(id=category_id)
                    service_type_obj = category_obj.service_type
                    service_family_obj = service_type_obj.family
                    
                    # Set the initial values
                    self.initial['service_family'] = service_family_obj.id
                    self.initial['service_type'] = service_type_obj.id
                    self.initial['category'] = category_obj.id
                    
                    # Update the querysets to include the initial values
                    if user.is_company_agent:
                        self.fields['service_family'].queryset = ServiceFamily.objects.filter(
                            company__in=assigned_companies
                        )
                    else:
                        self.fields['service_family'].queryset = ServiceFamily.objects.filter(company=company)
                    
                    self.fields['service_type'].queryset = ServiceType.objects.filter(family=service_family_obj)
                    self.fields['category'].queryset = ServiceCategory.objects.filter(service_type=service_type_obj)
                except ServiceCategory.DoesNotExist:
                    pass
            
            # Make description field optional
            self.fields['description'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        service_family = cleaned_data.get('service_family')
        service_type = cleaned_data.get('service_type')
        category = cleaned_data.get('category')
        
        if service_family and service_type:
            if service_type.family != service_family:
                raise forms.ValidationError("Selected service type does not belong to the selected service family")
        
        if service_type and category:
            if category.service_type != service_type:
                raise forms.ValidationError("Selected category does not belong to the selected service type")
        
        return cleaned_data

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
  