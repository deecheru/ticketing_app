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
    
    