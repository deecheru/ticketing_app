from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import ServiceFamily, ServiceType, ServiceCategory, Ticket, TicketAttachment, TicketComment
from accounts.models import Company, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from .forms import TicketForm, TicketCommentForm

class ServiceHierarchyTest(TestCase):
    def setUp(self):
        # Create a test company
        self.company = Company.objects.create(name='Test Company')
        
        # Create a test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company,
            is_staff=True
        )
        
        # Create service hierarchy
        self.family = ServiceFamily.objects.create(
            name='IT Services',
            description='IT related services',
            company=self.company
        )
        
        self.service_type = ServiceType.objects.create(
            name='Hardware Support',
            description='Hardware related issues',
            family=self.family
        )
        
        self.category = ServiceCategory.objects.create(
            name='Laptop Issues',
            description='Laptop related problems',
            service_type=self.service_type
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_service_family_creation(self):
        self.assertEqual(self.family.name, 'IT Services')
        self.assertEqual(self.family.company, self.company)

    def test_service_type_creation(self):
        self.assertEqual(self.service_type.name, 'Hardware Support')
        self.assertEqual(self.service_type.family, self.family)

    def test_service_category_creation(self):
        self.assertEqual(self.category.name, 'Laptop Issues')
        self.assertEqual(self.category.service_type, self.service_type)

class TicketCreationTest(TestCase):
    def setUp(self):
        # Create a test company
        self.company = Company.objects.create(name='Test Company')
        
        # Create test users
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company
        )
        
        self.staff_user = get_user_model().objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            company=self.company,
            is_staff=True
        )
        
        # Create service hierarchy
        self.family = ServiceFamily.objects.create(
            name='IT Services',
            description='IT related services',
            company=self.company
        )
        
        self.service_type = ServiceType.objects.create(
            name='Hardware Support',
            description='Hardware related issues',
            family=self.family
        )
        
        self.category = ServiceCategory.objects.create(
            name='Laptop Issues',
            description='Laptop related problems',
            service_type=self.service_type
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_create_ticket_with_valid_data(self):
        """Test creating a ticket with valid data"""
        ticket_data = {
            'title': 'Test Ticket',
            'description': 'Test Description',
            'status': 'OPEN',
            'priority': 'MEDIUM',
            'impact': 'PERSON',
            'category': self.category.id,
            'service_family': self.family.id,
            'service_type': self.service_type.id
        }
        
        response = self.client.post(reverse('create_ticket'), ticket_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        ticket = Ticket.objects.get(title='Test Ticket')
        self.assertEqual(ticket.description, 'Test Description')
        self.assertEqual(ticket.status, 'OPEN')
        self.assertEqual(ticket.priority, 'MEDIUM')
        self.assertEqual(ticket.impact, 'PERSON')
        self.assertEqual(ticket.category, self.category)
        self.assertEqual(ticket.created_by, self.user)
        self.assertEqual(ticket.company, self.company)

    def test_create_ticket_with_attachments(self):
        """Test creating a ticket with file attachments"""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"test file content",
            content_type="text/plain"
        )
        
        ticket_data = {
            'title': 'Test Ticket with Attachment',
            'description': 'Test Description',
            'status': 'OPEN',
            'priority': 'MEDIUM',
            'impact': 'PERSON',
            'category': self.category.id,
            'service_family': self.family.id,
            'service_type': self.service_type.id,
            'attachments': test_file
        }
        
        response = self.client.post(reverse('create_ticket'), ticket_data)
        self.assertEqual(response.status_code, 302)
        
        ticket = Ticket.objects.get(title='Test Ticket with Attachment')
        attachment = TicketAttachment.objects.get(ticket=ticket)
        self.assertEqual(attachment.filename, 'test.txt')
        self.assertEqual(attachment.uploaded_by, self.user)

    def test_create_ticket_with_comment(self):
        """Test creating a ticket with initial comment"""
        ticket_data = {
            'title': 'Test Ticket with Comment',
            'description': 'Test Description',
            'status': 'OPEN',
            'priority': 'MEDIUM',
            'impact': 'PERSON',
            'category': self.category.id,
            'service_family': self.family.id,
            'service_type': self.service_type.id,
            'text': 'Initial comment'
        }
        
        response = self.client.post(reverse('create_ticket'), ticket_data)
        self.assertEqual(response.status_code, 302)
        
        ticket = Ticket.objects.get(title='Test Ticket with Comment')
        comment = TicketComment.objects.get(ticket=ticket)
        self.assertEqual(comment.text, 'Initial comment')
        self.assertEqual(comment.created_by, self.user)

    def test_create_ticket_with_invalid_data(self):
        """Test creating a ticket with invalid data"""
        ticket_data = {
            'title': '',  # Empty title
            'description': 'Test Description',
            'status': 'OPEN',
            'priority': 'MEDIUM',
            'impact': 'PERSON',
            'category': self.category.id,
            'service_family': self.family.id,
            'service_type': self.service_type.id
        }
        
        response = self.client.post(reverse('create_ticket'), ticket_data)
        self.assertEqual(response.status_code, 200)
        
        # Get the form from the response context
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('title', form.errors)
        self.assertIn('This field is required', str(form.errors['title']))

    def test_create_ticket_with_invalid_category(self):
        """Test creating a ticket with invalid category"""
        ticket_data = {
            'title': 'Test Ticket',
            'description': 'Test Description',
            'status': 'OPEN',
            'priority': 'MEDIUM',
            'impact': 'PERSON',
            'category': 99999,  # Non-existent category ID
            'service_family': self.family.id,
            'service_type': self.service_type.id
        }
        
        response = self.client.post(reverse('create_ticket'), ticket_data)
        self.assertEqual(response.status_code, 200)
        
        # Get the form from the response context
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('category', form.errors)
        self.assertIn('Select a valid choice', str(form.errors['category']))

    def test_create_ticket_without_authentication(self):
        """Test creating a ticket without authentication"""
        self.client.logout()
        
        ticket_data = {
            'title': 'Test Ticket',
            'description': 'Test Description',
            'status': 'OPEN',
            'priority': 'MEDIUM',
            'impact': 'PERSON',
            'category': self.category.id,
            'service_family': self.family.id,
            'service_type': self.service_type.id
        }
        
        response = self.client.post(reverse('create_ticket'), ticket_data)
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        self.assertFalse(Ticket.objects.filter(title='Test Ticket').exists())

class TicketManagementTest(TestCase):
    def setUp(self):
        # Create a test company
        self.company = Company.objects.create(name='Test Company')
        
        # Create test users
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company
        )
        
        self.staff_user = get_user_model().objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            company=self.company,
            is_staff=True
        )
        
        # Create service hierarchy
        self.family = ServiceFamily.objects.create(
            name='IT Services',
            company=self.company
        )
        
        self.service_type = ServiceType.objects.create(
            name='Hardware Support',
            family=self.family
        )
        
        self.category = ServiceCategory.objects.create(
            name='Laptop Issues',
            service_type=self.service_type
        )
        
        # Create a test ticket
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test Description',
            status='OPEN',
            priority='MEDIUM',
            impact='PERSON',
            company=self.company,
            category=self.category,
            created_by=self.user,
            assigned_to=self.staff_user
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    
    def test_add_comment_to_ticket(self):
        """Test adding a comment to a ticket"""
        comment_data = {
            'text': 'Test Comment'
        }
        
        response = self.client.post(
            reverse('view_ticket', kwargs={'pk': self.ticket.pk}),
            comment_data
        )
        
        self.assertEqual(response.status_code, 302)
        comment = TicketComment.objects.get(ticket=self.ticket)
        self.assertEqual(comment.text, 'Test Comment')
        self.assertEqual(comment.created_by, self.user)

    def test_view_open_tickets(self):
        """Test viewing open tickets"""
        response = self.client.get(reverse('open_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/open_tickets.html')
        self.assertContains(response, 'Test Ticket')

    def test_view_closed_tickets(self):
        """Test viewing closed tickets"""
        # First close the ticket
        self.ticket.status = 'CLOSED'
        self.ticket.save()
        
        response = self.client.get(reverse('closed_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/closed_tickets.html')
        self.assertContains(response, 'Test Ticket')

    def test_search_tickets(self):
        """Test searching tickets"""
        response = self.client.get(reverse('open_tickets') + '?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ticket')

    def test_filter_tickets_by_status(self):
        """Test filtering tickets by status"""
        response = self.client.get(reverse('open_tickets') + '?status=OPEN')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ticket')

    def test_filter_tickets_by_priority(self):
        """Test filtering tickets by priority"""
        response = self.client.get(reverse('open_tickets') + '?priority=MEDIUM')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ticket')

    def test_filter_tickets_by_company(self):
        """Test filtering tickets by company"""
        response = self.client.get(reverse('open_tickets') + f'?company={self.company.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ticket')

class ServiceSelectionTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Company')
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_select_service_view(self):
        """Test the service selection view"""
        response = self.client.get(reverse('select_service'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/select_service.html')

    def test_get_service_types(self):
        """Test getting service types via API"""
        family = ServiceFamily.objects.create(
            name='IT Services',
            company=self.company
        )
        service_type = ServiceType.objects.create(
            name='Hardware Support',
            family=family
        )
        
        response = self.client.get(
            reverse('get_service_types') + f'?family_id={family.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hardware Support')

    def test_get_service_categories(self):
        """Test getting service categories via API"""
        family = ServiceFamily.objects.create(
            name='IT Services',
            company=self.company
        )
        service_type = ServiceType.objects.create(
            name='Hardware Support',
            family=family
        )
        category = ServiceCategory.objects.create(
            name='Laptop Issues',
            service_type=service_type
        )
        
        response = self.client.get(
            reverse('get_service_categories') + f'?type_id={service_type.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Laptop Issues')
