def show_settings(settings, action):
    import guardian
    from django.utils.termcolors import colorize

    guardian_path = guardian.__path__[0]
    msg = "django-guardian module's path: %r" % guardian_path
    print(colorize(msg, fg='magenta'))
    db_conf = settings.DATABASES['default']
    output = []
    msg = "Starting {} for db backend: {}".format(action, db_conf['ENGINE'])
    embracer = '=' * len(msg)
    output.append(msg)
    for key in sorted(db_conf.keys()):
        if key == 'PASSWORD':
            value = '****************'
        else:
            value = db_conf[key]
        line = '    {}: "{}"'.format(key, value)
        output.append(line)
    embracer = colorize('=' * len(max(output, key=lambda s: len(s))),
                        fg='green', opts=['bold'])
    output = [colorize(line, fg='blue') for line in output]
    output.insert(0, embracer)
    output.append(embracer)
    print('\n'.join(output))
