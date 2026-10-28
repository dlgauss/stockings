from django.conf import settings
from django.urls import translate_url
from django.utils.translation import get_language


def language_links(request):
    """The current page's URL in every language, for the RU/RO switch and hreflang tags."""
    current = get_language()
    return {
        'language_links': [
            {
                'code': code,
                'url': translate_url(request.path, code),
                'active': code == current,
            }
            for code, _name in settings.LANGUAGES
        ],
    }
