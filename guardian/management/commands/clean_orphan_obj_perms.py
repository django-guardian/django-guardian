from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand

from guardian.utils import clean_orphan_obj_perms


class Command(NoArgsCommand):
    """
    clean_orphan_obj_perms command is a tiny wrapper around
    :func:`guardian.utils.clean_orphan_obj_perms`.

    Usage::

        $ python manage.py clean_orphan_obj_perms
        Removed 11 object permission entries with no targets

    """
    help = "Removes object permissions with not existing targets"

    def handle_noargs(self, **options):
        removed = clean_orphan_obj_perms()
        if options['verbosity'] > 0:
            print("Removed %d object permission entries with no targets" %
                removed)

