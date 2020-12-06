import pprint

from django.test import TestCase, Client
from django.urls import reverse
from user.models import User,Profile

class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='Fenna96')
        user.set_password('oscarpro96')
        user.save()
        self.redirect_url = '/?next='
        self.login_url = reverse("user:login")
        self.enter_url = reverse('user:enter')
        self.registration_url = reverse('user:registration')
        self.complete_url = reverse('user:complete')
        self.logout_url = reverse('user:logout')

    def test_login_methods(self):
        get_response = self.client.get(self.login_url)
        post_response = self.client.post(self.login_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

    def test_logout_methods(self):
        get_response = self.client.get(self.logout_url)
        post_response = self.client.post(self.logout_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)

    def test_register_methods(self):
        get_response = self.client.get(self.registration_url)
        post_response = self.client.post(self.registration_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

    def test_enter_methods(self):
        get_response = self.client.get(self.enter_url)
        post_response = self.client.post(self.enter_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302) #no data

    def test_enter_validated_post(self):
        post_response = self.client.post(self.enter_url,{
            'username':'Fenna96',
            'password':'oscarpro96'
        })
        self.assertEquals(post_response.status_code, 302)
        self.assertEquals(post_response.url, reverse('manager:index'))

    def test_enter_wrong_username(self):
        post_response = self.client.post(self.enter_url,{
            'username':'Fenna97',
            'password':'oscarpro96'
        })
        self.assertEquals(post_response.status_code, 302)
        self.assertEquals(post_response.context['error'], 'Wrong username or password.')

    def test_enter_wrong_password(self):
        self.client.logout()
        post_response = self.client.post(self.enter_url,{
            'username':'Fenna96',
            'password':'oscarpro97'
        })
        self.assertEquals(post_response.status_code, 302)
        self.assertEquals(post_response.context['error'], 'Wrong username or password.')

    def test_complete_methods(self):
        get_response = self.client.get(self.complete_url)
        post_response = self.client.post(self.complete_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302) #no data

    def test_complete_validated_post(self):
        data = {
            'username': 'Martina',
            'password': 'marti',
            'email': 'marti.levizzani@gmail.com',
            'biography': '-',
            'mobile': 3384014188,
            'name': 'Martina',
            'surname': 'Levizzani',
        }

        post_response = self.client.post(self.complete_url,data)

        self.assertEquals(post_response.status_code, 302)
        self.assertEquals(post_response.url, reverse('manager:index'))

    def test_complete_user_created(self):
        data = {
            'username': 'Martina',
            'password': 'marti',
            'email': 'marti.levizzani@gmail.com',
            'biography': '-',
            'mobile': 3384014188,
            'name': 'Martina',
            'surname': 'Levizzani',
        }

        post_response = self.client.post(self.complete_url, data)

        self.assertTrue(User.objects.get(username='Martina'))

    def test_complete_profile_created(self):
        data = {
            'username': 'Martina',
            'password': 'marti',
            'email': 'marti.levizzani@gmail.com',
            'biography': '-',
            'mobile': 3384014188,
            'name': 'Martina',
            'surname': 'Levizzani',
        }

        post_response = self.client.post(self.complete_url, data)

        self.assertTrue(Profile.objects.get(user=User.objects.get(username='Martina')))

    def test_complete_already_in_use(self):
        data = {
            'username': 'Martina',
            'password': 'marti',
            'email': 'marti.levizzani@gmail.com',
            'biography': '-',
            'mobile': 3384014188,
            'name': 'Martina',
            'surname': 'Levizzani',
        }

        user = User.objects.create(username='Martina')
        user.save()

        post_response = self.client.post(self.complete_url,data)

        self.assertEquals(post_response.status_code, 302)
        self.assertEquals(post_response.context['error'], 'Username or email already in use.')

    def test_complete_form_not_valid(self):
        data = {
            'username': 'Martina',
            'password': 'marti',
            'email': 'marti.levizzani@gmail.com',
            'biography': '-',
            'mobile': 3384014188,
            'name': 'Martina!',
            'surname': 'Levizzani',
        }

        post_response = self.client.post(self.complete_url,data)

        self.assertEquals(post_response.status_code, 302)
        self.assertEquals(len(post_response.context['form'].errors), 1)

