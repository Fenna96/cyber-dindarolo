from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator, DecimalValidator
from django.db import models

# Create your models here.
from django.db.models import ImageField

DEFAULT_PIC_FILE = "static/profile_pics/default-avatar.jpg"
PROFILE_PIC_FOLDER = "static/profile_pics/"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    mobile = models.IntegerField()
    biography = models.CharField(max_length=400)
    profile_image = ImageField(
        upload_to=PROFILE_PIC_FOLDER, blank=True, default=DEFAULT_PIC_FILE
    )

    def __str__(self):
        return f"Profile of {self.user}"
