import re

from django.contrib.auth import authenticate
from django.core.validators import EmailValidator
from rest_framework import serializers

from .serializers import ProfileSerializer, CatalogSerializer, ProductSerializer

#IMPORTING USER MODELS
from user.models import User,Profile

#IMPORTING ALL OTHER MODELS
from manager.models import Balance,Catalog,Category,Product,Product_pricetracker,Transaction

#USER FORMS
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='Enter your username',required=True)
    email = serializers.CharField(label='Enter your email', validators=[EmailValidator(message='Not a valid email address')], required=True)
    password = serializers.CharField(label='Enter your password',required=True)

    class Meta:
        model = Profile
        fields = ['username', 'email', 'password', 'name', 'surname', 'mobile', 'biography', 'profile_image']

    def validate(self,data):
        username = data['username']
        if len(username) > 10:
            raise serializers.ValidationError(('10 characters max'), code='user_limit')

        name = data['name']
        if not re.fullmatch('[a-zA-Z]+', name):
            raise serializers.ValidationError(("You can't have special characters in your name, unless you're Musk"),code='name_number')

        surname = data['surname']
        if not re.fullmatch('[a-zA-Z]+', surname):
            raise serializers.ValidationError(("You can't have special characters in your name, unless you're Musk"), code='surname_number')

        mobile = data['mobile']
        phone = str(mobile)
        if len(phone) > 10 or len(phone) < 9:
            raise serializers.ValidationError(('Not a valid phone number'), code='phone')

        if 'profile_image' not in data.keys():
            data['profile_image'] = None

        return data

#MARKET FORM
class insertSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=20)
    category = serializers.CharField(max_length=20)
    class Meta:
        model = Catalog
        fields = ['name','category','quantity','price']

    def validate(self,data):
        category = data['category']
        if not Category.objects.filter(name=category):
            raise serializers.ValidationError(('Category not found'), code='not_found')

        price = data['price']
        if int(price) <= 0:
            raise serializers.ValidationError(('Price cant be negative'), code='negative_price')

        quantity = data['quantity']
        if int(quantity) <= 0:
            raise serializers.ValidationError(('Quantity cant be negative'), code='negative_price')

        return data

class buySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)

class removeSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class searchSerializer(serializers.Serializer):
    typed = serializers.CharField(max_length=20)

class modifySerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='Enter your username', required=True)
    email = serializers.CharField(label='Enter your email',validators=[EmailValidator(message='Not a valid email address')], required=True)

    class Meta:
        model = Profile
        fields = ['username','email','name', 'surname', 'mobile', 'biography']

    def validate(self,data):

        name = data['name']
        if not re.fullmatch('[a-zA-Z]+', name):
            raise serializers.ValidationError(("You can't have special characters in your name, unless you're Musk"),code='name_number')

        surname = data['surname']
        if not re.fullmatch('[a-zA-Z]+', surname):
            raise serializers.ValidationError(("You can't have special characters in your name, unless you're Musk"), code='surname_number')

        mobile = data['mobile']
        phone = str(mobile)
        if len(phone) > 10 or len(phone) < 9:
            raise serializers.ValidationError(('Not a valid phone number'), code='phone')

        return data

