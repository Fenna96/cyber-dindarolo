from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator, DecimalValidator
from django.db import models
# Create your models here.
from django.db.models import ImageField

DEFAULT_PIC = "static/profile_pics/default-avatar.jpg"
PROFILE_PIC = "static/profile_pics/"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    mobile = models.IntegerField()
    biography = models.CharField(max_length=400)
    profile_image = ImageField(upload_to=PROFILE_PIC, blank=True, default=DEFAULT_PIC)


    def __str__(self):
        return f'Profile of {self.user}'
