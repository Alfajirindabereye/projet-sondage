from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        resp = self.client.post(reverse('accounts:register'), {
            'username': 'testuser', 'email': 'test@example.com',
            'password1': 'CorrectHorseBattery9!', 'password2': 'CorrectHorseBattery9!',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(resp.context['user'].is_authenticated)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(username='a', email='dup@example.com', password='x12345678!')
        resp = self.client.post(reverse('accounts:register'), {
            'username': 'b', 'email': 'dup@example.com',
            'password1': 'CorrectHorseBattery9!', 'password2': 'CorrectHorseBattery9!',
        })
        self.assertEqual(resp.status_code, 200)  # re-renders form with error
        self.assertFalse(User.objects.filter(username='b').exists())


class LoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='bob', email='bob@example.com', password='CorrectHorseBattery9!')

    def test_login_with_username(self):
        resp = self.client.post(reverse('accounts:login'), {'username': 'bob', 'password': 'CorrectHorseBattery9!'})
        self.assertEqual(resp.status_code, 302)

    def test_login_with_email(self):
        resp = self.client.post(reverse('accounts:login'), {'username': 'bob@example.com', 'password': 'CorrectHorseBattery9!'})
        self.assertEqual(resp.status_code, 302)

    def test_lockout_after_repeated_failures(self):
        for _ in range(5):
            self.client.post(reverse('accounts:login'), {'username': 'bob', 'password': 'wrong'})
        resp = self.client.post(reverse('accounts:login'), {'username': 'bob', 'password': 'wrong'})
        self.assertContains(resp, "Trop de tentatives")
