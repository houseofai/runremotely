def decorate(func):
    print(u"Je suis dans la fonction 'decorate' et je décore '%s'." % func.__name__)
    print(u"Exécution de la fonction '%s'." % func.__name__)
    return func
