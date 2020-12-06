from django.test import SimpleTestCase
from django.urls import reverse,resolve
from user.views import user_login,user_logout,execute_login,execute_registration,registration

class TestUrls(SimpleTestCase):

    def test_user_login_url(self):
        self.assertEquals(resolve(reverse('user:login')).func, user_login)
    def test_execute_login_url(self):
        self.assertEquals(resolve(reverse('user:enter')).func, execute_login)
    def test_registration_url(self):
        self.assertEquals(resolve(reverse('user:registration')).func, registration)
    def test_execute_registration_url(self):
        self.assertEquals(resolve(reverse('user:complete')).func, execute_registration)
    def test_user_logout_url(self):
        self.assertEquals(resolve(reverse('user:logout')).func, user_logout)
