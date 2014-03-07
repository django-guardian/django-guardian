from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime


class CustomUser(AbstractUser):
    real_username = models.CharField(max_length=120, unique=True)
    birth_date = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'real_username'

    def save(self, *args, **kwargs):
        if not self.real_username:
            self.real_username = self.username
        return super(CustomUser, self).save(*args, **kwargs)


def get_custom_anon_user(User):
    return User(
        real_username='AnonymousUser',
        birth_date=datetime.date(1410, 7, 15),
    )
