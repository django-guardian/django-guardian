import guardian


def version(request):
    return {'version': guardian.get_version()}
