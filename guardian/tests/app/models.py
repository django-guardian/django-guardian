from django.db import models

class Keycard(models.Model):
    key = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        app_label = 'guardian'
        permissions = (
            ('can_use_keycard', 'Can use Keycard'),
            ('can_suspend_keycard', 'Can suspend Keycard'),
        )


class KeyValue(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    value = models.TextField(null=True)

    class Meta:
        app_label = 'guardian'

