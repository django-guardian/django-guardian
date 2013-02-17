"""
Exceptions used by django-guardian. All internal and guardian-specific errors
should extend GuardianError class.
"""
from __future__ import unicode_literals


class GuardianError(Exception):
    pass

class NotUserNorGroup(GuardianError):
    pass

class ObjectNotPersisted(GuardianError):
    pass

class WrongAppError(GuardianError):
    pass

class MixedContentTypeError(GuardianError):
    pass

