from django.core.management.base import NoArgsCommand

from guardian.utils import clean_orphan_obj_perms


class Command(NoArgsCommand):
    help = "Removes object permissions with not existing targets"

    def handle_noargs(self, **options):
        removed = clean_orphan_obj_perms()
        if options['verbosity'] > 0:
            print "Removed %d object permission entries with no targets" %\
                removed

