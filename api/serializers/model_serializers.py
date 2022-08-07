from typing import Optional
from manager.models import (
    Balance,
    CatalogItem,
    Category,
    Product,
    Product_pricetracker,
    Transaction,
)
from rest_framework import serializers
from user.models import Profile, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = "__all__"

    def validate_user(self, value: int):
        user: Optional[User] = User.objects.filter(id=value).first()
        assert user is not None, f"Catalog item pointing to non-existant user {value}"
        return user.username


class PricetrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_pricetracker
        fields = "__all__"
