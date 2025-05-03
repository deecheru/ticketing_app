# accounts/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class LoginTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
    def test_user_can_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)

class LogoutTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='logoutpassword'
        )
        self.client.login(username='logoutuser', password='logoutpassword')

    def test_user_can_logout(self):
        self.assertTrue(self.client.session.get('_auth_user_id'))
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get('_auth_user_id'))
        self.assertRedirects(response, reverse('login'))

class DashboardTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='dashboarduser',
            email='dashboard@example.com',
            password='dashboardpassword'
        )
        self.client.login(username='dashboarduser', password='dashboardpassword')

    def test_dashboard_page_loads_for_authenticated_user(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')
