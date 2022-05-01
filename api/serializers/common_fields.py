import re
from typing import Any, Dict

from django.core.validators import EmailValidator
from rest_framework import serializers

USERNAME = serializers.CharField(
    label="Enter your username", max_length=10, required=True
)
"Profile username field, used in different serializers."
EMAIL = serializers.CharField(
    label="Enter your email",
    validators=[EmailValidator(message="Not a valid email address")],
    required=True,
)
"Profile email field, used in different serializers."
PASSWORD = serializers.CharField(label="Enter your password", required=True)
"Profile password field, used in different serializers."


def customProfileValidation(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom validation for a user profile. It ensure that:

    -   surname and name are composed only of letters
    -   mobile is a valid phone number
    -   profile image is either defined or set to None

    Parameters
    ----------
    data: Dict[str, Any]
        data to validate

    Returns
    -------
    Dict[str, Any]
        validated data
    """
    name = data["name"]
    if not re.fullmatch("[a-zA-Z]+", name):
        raise serializers.ValidationError(
            ("You can't have special characters in your name, unless you're Musk"),
            code="name_number",
        )

    surname = data["surname"]
    if not re.fullmatch("[a-zA-Z]+", surname):
        raise serializers.ValidationError(
            ("You can't have special characters in your name, unless you're Musk"),
            code="surname_number",
        )

    mobile = data["mobile"]
    phone = str(mobile)
    if len(phone) > 10 or len(phone) < 9:
        raise serializers.ValidationError(("Not a valid phone number"), code="phone")

    if "profile_image" not in data:
        data["profile_image"] = None

    return data
