import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    birth_date = models.DateField(null=True, blank=True)


def get_custom_anon_user(User):
    return User(
        username='AnonymousUser',
        birth_date=datetime.date(1410, 7, 15),
    )
