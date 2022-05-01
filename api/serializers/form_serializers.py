import re

from api.serializers.common_fields import (
    EMAIL,
    PASSWORD,
    USERNAME,
    customProfileValidation,
)
from manager.models import CatalogItem, Category
from rest_framework import serializers
from user.models import Profile


class LoginSerializer(serializers.Serializer):
    username = USERNAME
    password = PASSWORD


class RegistrationSerializer(serializers.ModelSerializer):
    username = USERNAME
    email = EMAIL
    password = PASSWORD

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "password",
            "name",
            "surname",
            "mobile",
            "biography",
            "profile_image",
        ]

    def validate(self, data):
        return customProfileValidation(data)


class InsertSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=20, required=True)
    category = serializers.CharField(max_length=20, required=True)

    class Meta:
        model = CatalogItem
        fields = ["name", "category", "quantity", "price"]

    def validate(self, data):
        category = data["category"]
        if not Category.objects.filter(name=category):
            raise serializers.ValidationError(("Category not found"), code="not_found")

        price = data["price"]
        if int(price) <= 0:
            raise serializers.ValidationError(
                ("Price can't be negative"), code="negative_price"
            )

        quantity = data["quantity"]
        if int(quantity) <= 0:
            raise serializers.ValidationError(
                ("Quantity can't be negative"), code="negative_price"
            )

        return data


class BuySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, default=1)


class RemoveSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)


class SearchSerializer(serializers.Serializer):
    typed = serializers.CharField(max_length=20, required=True)


class ModifySerializer(serializers.ModelSerializer):
    username = USERNAME
    email = EMAIL

    class Meta:
        model = Profile
        fields = ["username", "email", "name", "surname", "mobile", "biography"]

    def validate(self, data):
        return customProfileValidation(data)
