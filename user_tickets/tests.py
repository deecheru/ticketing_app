from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import ServiceFamily, ServiceType, ServiceCategory, Ticket, TicketAttachment, TicketComment
from accounts.models import Company
from django.core.files.uploadedfile import SimpleUploadedFile

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

class TicketTest(TestCase):
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

    def test_ticket_creation(self):
        self.assertEqual(self.ticket.title, 'Test Ticket')
        self.assertEqual(self.ticket.status, 'OPEN')
        self.assertEqual(self.ticket.created_by, self.user)
        self.assertEqual(self.ticket.assigned_to, self.staff_user)

    def test_ticket_view(self):
        response = self.client.get(reverse('view_ticket', kwargs={'pk': self.ticket.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/view_ticket.html')

    def test_ticket_edit(self):
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.post(
            reverse('edit_ticket', kwargs={'pk': self.ticket.pk}),
            {
                'title': 'Updated Ticket',
                'description': 'Updated Description',
                'priority': 'HIGH',
                'impact': 'DEPARTMENT',
                'category': self.category.id
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful edit
        updated_ticket = Ticket.objects.get(pk=self.ticket.pk)
        self.assertEqual(updated_ticket.title, 'Updated Ticket')

    def test_ticket_comment(self):
        response = self.client.post(
            reverse('view_ticket', kwargs={'pk': self.ticket.pk}),
            {'text': 'Test Comment'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful comment
        comment = TicketComment.objects.filter(ticket=self.ticket).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.text, 'Test Comment')

class TicketAttachmentTest(TestCase):
    def setUp(self):
        # Create a test company
        self.company = Company.objects.create(name='Test Company')
        
        # Create a test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company
        )
        
        # Create a test ticket
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test Description',
            status='OPEN',
            priority='MEDIUM',
            impact='PERSON',
            company=self.company,
            created_by=self.user
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_ticket_attachment(self):
        # Create a test file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"test file content",
            content_type="text/plain"
        )
        
        # Create attachment
        attachment = TicketAttachment.objects.create(
            ticket=self.ticket,
            file=test_file,
            filename='test.txt',
            uploaded_by=self.user
        )
        
        self.assertEqual(attachment.filename, 'test.txt')
        self.assertEqual(attachment.ticket, self.ticket)
        self.assertEqual(attachment.uploaded_by, self.user)

class TicketListViewTest(TestCase):
    def setUp(self):
        # Create a test company
        self.company = Company.objects.create(name='Test Company')
        
        # Create a test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company
        )
        
        # Create test tickets
        self.open_ticket = Ticket.objects.create(
            title='Open Ticket',
            description='Open Ticket Description',
            status='OPEN',
            priority='MEDIUM',
            impact='PERSON',
            company=self.company,
            created_by=self.user
        )
        
        self.closed_ticket = Ticket.objects.create(
            title='Closed Ticket',
            description='Closed Ticket Description',
            status='CLOSED',
            priority='LOW',
            impact='PERSON',
            company=self.company,
            created_by=self.user
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_open_tickets_view(self):
        response = self.client.get(reverse('open_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/open_tickets.html')
        self.assertContains(response, 'Open Ticket')
        self.assertNotContains(response, 'Closed Ticket')

    def test_closed_tickets_view(self):
        response = self.client.get(reverse('closed_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/closed_tickets.html')
        self.assertContains(response, 'Closed Ticket')
        self.assertNotContains(response, 'Open Ticket')
