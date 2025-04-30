# accounts/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Profile

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

    def test_dashboard_page_redirects_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

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

class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='profilepassword'
        )
        self.client.login(username='profileuser', password='profilepassword')
        #Profile.objects.create(user=self.user) # Ensure a profile exists

    def test_profile_page_loads_for_authenticated_user(self):
        response = self.client.get(reverse('profile_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_page_redirects_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(reverse('profile_view'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('profile_view'))

class ProfileUpdateViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='updateuser',
            email='update@example.com',
            password='updatepassword',
            first_name='Old',
            last_name='Name'
        )
        self.client.login(username='updateuser', password='updatepassword')
        #Profile.objects.create(user=self.user, job_title='Old Job')

    def test_profile_update_page_loads_for_authenticated_user(self):
        response = self.client.get(reverse('profile_update'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile_update.html')
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)

    def test_profile_update_redirects_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(reverse('profile_update'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('profile_update'))

    def test_user_can_update_profile(self):
        # First, make sure the Profile exists for the user
        if not hasattr(self.user, 'profile'):
            from accounts.models import Profile
            Profile.objects.create(user=self.user, role='admin')
        
        # Submit the form data
        response = self.client.post(
            reverse('profile_update'),
            {
                'first_name': 'New',
                'last_name': 'Name',
                'email': self.user.email,
                'role': 'client',  # Must match one of the ROLE_CHOICES from your model
                'job_title': 'New Job',
                'phone': '123-456-7890',
                'bio': 'Updated bio information.',
                'timezone': 'America/New_York',
                'language': 'en',
                'department': 'Engineering',
                'email_notifications': 'on',  # For checkboxes, use 'on' or True
            }
        )
        
        # Check for redirect (successful form submission)
        if response.status_code != 302:
            # Form submission failed - print debug info if available
            if 'user_form' in response.context:
                print(f"User Form Errors: {response.context['user_form'].errors}")
            if 'profile_form' in response.context:
                print(f"Profile Form Errors: {response.context['profile_form'].errors}")
            self.fail("Form submission failed - did not redirect")
        
        # Check that we got redirected to profile_view
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile_view'))
        
        # Verify the database updates
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.profile.job_title, 'New Job')
        self.assertEqual(self.user.profile.phone, '123-456-7890')
        self.assertEqual(self.user.profile.bio, 'Updated bio information.')
        
        # Verify the database was updated correctly
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.profile.job_title, 'New Job')
        self.assertEqual(self.user.profile.phone, '123-456-7890')
        self.assertEqual(self.user.profile.bio, 'Updated bio information.')

    def test_profile_update_with_invalid_data(self):
        response = self.client.post(
            reverse('profile_update'),
            {
                'first_name': '', # Invalid data
                'last_name': 'Name',                
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile_update.html')
        self.assertIn('user_form', response.context) # Ensure the form is in the context
        self.assertIn('profile_form', response.context) # Ensure the profile form is in the context
        self.assertFormError(response.context['user_form'], 'first_name', 'This field is required.')
        self.assertContains(response, 'Please correct the errors below.')

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Old') # Ensure data wasn't saved