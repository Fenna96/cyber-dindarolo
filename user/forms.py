import re

from django import forms
from django.core.validators import EmailValidator
from django.forms import ModelForm
from user.models import Profile


class ProfileForm(ModelForm):
    username = forms.CharField(label='Enter your username')
    email = forms.CharField(label='Enter your email', validators=[EmailValidator(message='Not a valid email address')])
    password = forms.CharField(label='Enter your password', widget=forms.PasswordInput())

    class Meta:
        model = Profile
        fields = ['username', 'email', 'password', 'name', 'surname', 'mobile', 'biography', 'profile_image']

    def clean_username(self):
        data = self.cleaned_data
        username = data['username']
        if len(username) > 10:
            raise forms.ValidationError('10 characters max', code='user_limit')
        return username

    def clean_name(self):
        data = self.cleaned_data
        name = data['name']
        if not re.fullmatch('[a-zA-Z]+', name):
            raise forms.ValidationError("You can't have special characters in your name, unless you're Musk",
                                        code='name_number')
        return name

    def clean_surname(self):
        data = self.cleaned_data
        surname = data['surname']
        if not re.fullmatch('[a-zA-Z]+', surname):
            raise forms.ValidationError("You can't have special characters in your name, unless you're Musk",
                                        code='surname_number')
        return surname

    def clean_mobile(self):
        data = self.cleaned_data
        mobile = data['mobile']
        phone = str(mobile)
        if len(phone) > 10 or len(phone) < 9:
            raise forms.ValidationError('Not a valid phone number', code='phone')
        return mobile

    def clean_profile_image(self):
        data = self.cleaned_data
        profile_image = data['profile_image']
        return profile_image


class LoginForm(forms.Form):
    username = forms.CharField(label='Enter your username')
    password = forms.CharField(label='Enter your password', widget=forms.PasswordInput())
