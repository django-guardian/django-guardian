""" django-guardian custom signals
"""
import django


get_perms = django.dispatch.Signal(providing_args=["user", "obj"])
