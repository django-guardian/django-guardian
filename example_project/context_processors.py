from django.contrib.flatpages.models import FlatPage

def flats(request):
    return {
        'flats': FlatPage.objects.all().values('title', 'url'),
    }

