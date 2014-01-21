from gaurdian.compat import mock

try:
    from unittest import mock  # Since Python 3.3 mock is is in stdlib
except ImportError:
    import mock # pyflakes:ignore
