from rest_framework import serializers

#IMPORTING USER MODELS
from user.models import User,Profile

#IMPORTING ALL OTHER MODELS
from manager.models import Balance,Catalog,Category,Product,Product_pricetracker,Transaction

#USER SERIALIZER
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','email']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


#MANAGER SERIALIZERS
class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog
        fields = '__all__'

class PricetrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_pricetracker
        fields = '__all__'


