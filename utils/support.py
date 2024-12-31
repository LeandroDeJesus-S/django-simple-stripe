def get_user_lang(request, default: str | None = None):
    langs: str = request.META.get('HTTP_ACCEPT_LANGUAGE')
    
    if langs is not None:
        lang = langs.split(',')[0]
        return lang
    
    elif default is not None:
        return default
