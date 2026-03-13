from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.checks import Tags, Warning, register
from django.core.exceptions import FieldDoesNotExist


def _user_model_has_is_active_field() -> bool:
    """Check whether the current user model has an ``is_active`` field."""
    try:
        get_user_model()._meta.get_field("is_active")
        return True
    except FieldDoesNotExist:
        return False


# noinspection PyUnusedLocal
@register(Tags.compatibility)
def check_settings(app_configs, **kwargs):
    """Check that settings are implemented properly
    :param app_configs: a list of apps to be checks or None for all
    :param kwargs: keyword arguments
    :return: a list of errors
    """
    checks = []
    if "guardian.backends.ObjectPermissionBackend" not in settings.AUTHENTICATION_BACKENDS:
        msg = (
            "Guardian authentication backend is not hooked. You can add this in settings as eg: "
            "`AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', "
            "'guardian.backends.ObjectPermissionBackend')`."
        )
        checks.append(Warning(msg, id="guardian.W001"))
    return checks


@register(Tags.compatibility)
def check_active_users_only(app_configs, **kwargs):
    checks = []
    if getattr(settings, "GUARDIAN_ACTIVE_USERS_ONLY", False) and not _user_model_has_is_active_field():
        checks.append(
            Warning(
                "GUARDIAN_ACTIVE_USERS_ONLY is enabled but the user model "
                "does not have an 'is_active' field. The setting will have no effect.",
                id="guardian.W002",
            )
        )
    return checks
