from django.core.management.base import BaseCommand

from guardian.utils import clean_orphan_obj_perms


class Command(BaseCommand):
    """A wrapper around `guardian.utils.clean_orphan_obj_perms`.

    Seeks and removes all object permissions entries pointing at non-existing targets.
    Returns the number of objects removed.

    Example:
        ```shell
        $ python manage.py clean_orphan_obj_perms
        Removed 11 object permission entries with no targets
        ```
    """
    help = "Removes object permissions with not existing targets"

    def handle(self, **options):
        removed = clean_orphan_obj_perms()
        if options['verbosity'] > 0:
            print("Removed %d object permission entries with no targets" %
                  removed)
