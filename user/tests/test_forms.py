import pprint

from django.test import TestCase, Client
from django.urls import reverse
from user.models import User,Profile
from user.forms import LoginForm,ProfileForm

class TestForms(TestCase):

    def test_login_form(self):
        form = LoginForm(data={
            'username':'Martina',
            'password':'marti'
        })

        self.assertTrue(form.is_valid())

    def test_login_form_username_required(self):
        form = LoginForm(data={
            'password':'marti'
        })

        self.assertFalse(form.is_valid())

    def test_login_form_password_required(self):
        form = LoginForm(data={
            'username':'Martina'
        })

        self.assertFalse(form.is_valid())

    def test_profile_form(self):
        form = ProfileForm(data={
            'username':'Martina',
            'password':'marti',
            'email':'marti.levizzani@gmail.com',
            'biography':'-',
            'mobile':3384014188,
            'name':'Martina',
            'surname':'Levizzani',
        })

        self.assertTrue(form.is_valid())

    def test_profile_form_username_lenght(self):
        form = ProfileForm(data={
            'username':'Martinaaaaaaaa',
            'password':'marti',
            'email':'marti.levizzani@gmail.com',
            'biography':'-',
            'mobile':3384014188,
            'name':'Martina',
            'surname':'Levizzani',
        })

        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors),1)

    def test_profile_form_mobile_lenght(self):
        form = ProfileForm(data={
            'username':'Martina',
            'password':'marti',
            'email':'marti.levizzani@gmail.com',
            'biography':'-',
            'mobile':338401418811111,
            'name':'Martina',
            'surname':'Levizzani',
        })

        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors),1)

    def test_profile_form_valid_email(self):
        form = ProfileForm(data={
            'username':'Martina',
            'password':'marti',
            'email':'marti.levizzani?gmail.com',
            'biography':'-',
            'mobile':3384014188,
            'name':'Martina',
            'surname':'Levizzani',
        })

        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors),1)

    def test_profile_form_all_required(self):
        form = ProfileForm(data={
        })

        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors),7)

    def test_profile_name_only_letters(self):
        form = ProfileForm(data={
            'username':'Martina',
            'password':'marti',
            'email':'marti.levizzani@gmail.com',
            'biography':'-',
            'mobile':3384014188,
            'name':'Martina!',
            'surname':'Levizzani?',
        })

        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors),2)




