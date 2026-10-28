from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language, gettext, gettext_lazy as _, override
from django.views.decorators.http import require_GET

from . import cities, photon
from .forms import OrderForm
from .models import LandingSettings, LegalPage, Review, Size

LEGAL_TITLES = {
    LegalPage.Kind.PRIVACY: _('Privacy policy'),
    LegalPage.Kind.TERMS: _('Terms of use'),
    LegalPage.Kind.RETURNS: _('Return policy'),
}


def _page_context(content=None, **extra):
    """Data every page needs: the placeholder values and which footer links to show."""
    return {
        'content': content or LandingSettings.load(),
        'legal_pages': list(
            LegalPage.objects.exclude(body_ro='', body_ru='').values_list('kind', flat=True)
        ),
        **extra,
    }


def home(request):
    content = LandingSettings.load()
    sizes = list(Size.objects.filter(is_active=True).values_list('label', flat=True))

    if request.method == 'POST':
        form = OrderForm(request.POST, sizes=sizes)
        if form.is_valid():
            if form.cleaned_data['website']:
                # Honeypot filled in: a bot. Pretend it worked, save nothing.
                return redirect('landing:thanks')
            order = form.save(commit=False)
            order.unit_price = content.price
            order.currency = content.currency
            order.language = get_language()
            order.save()
            request.session['order_id'] = order.pk
            return redirect('landing:thanks')
    else:
        form = OrderForm(sizes=sizes)

    return render(request, 'landing/home.html', _page_context(
        content,
        form=form,
        reviews=Review.objects.filter(is_active=True),
        combo_data={
            'cities': cities.options(get_language()),
            'popularCount': cities.POPULAR_COUNT,
            'text': _combo_text(),
        },
    ))


def _combo_text():
    """Messages shown inside the city/street dropdowns (static/landing/js/landing.js)."""
    return {
        'popular': gettext('Popular cities'),
        'searching': gettext('Searching…'),
        'noResults': gettext('Nothing found. You can keep what you typed.'),
        'useTyped': gettext('Use “%s”'),
        'streetStart': gettext('Start typing the street name'),
        'cityFirst': gettext('Choose the city first for more accurate suggestions'),
        'latinOnly': gettext('Street suggestions work in Latin letters, e.g. Mihai Viteazul'),
        'houseNumber': gettext('Don’t forget the house number'),
    }


def thanks(request):
    return render(request, 'landing/thanks.html', _page_context(
        order_id=request.session.pop('order_id', None),
    ))


def legal(request, kind):
    page = get_object_or_404(LegalPage, kind=kind)
    if not page.body:
        raise Http404
    return render(request, 'landing/legal.html', _page_context(
        page=page,
        title=LEGAL_TITLES[page.kind],
    ))


def page_not_found(request, exception):
    """404 in the site's design. Django uses it only when DEBUG is off.

    The language switch leads to the main page, not to the same missing page in another language.
    """
    current = get_language()
    language_links = []
    for code, _name in settings.LANGUAGES:
        with override(code):
            language_links.append({
                'code': code, 'url': reverse('landing:home'), 'active': code == current,
            })
    return render(request, 'landing/404.html', _page_context(
        language_links=language_links,
    ), status=404)


@require_GET
def address_suggest(request):
    query = request.GET.get('q', '').strip()
    if not 2 <= len(query) <= 100:
        return JsonResponse({'results': []})

    if request.GET.get('kind') == 'street':
        try:
            lat = float(request.GET['lat'])
            lon = float(request.GET['lon'])
        except (KeyError, ValueError):
            lat = lon = None
        city = request.GET.get('city', '').strip()[:150]
        results = photon.search_streets(query, city, lat, lon)
    else:
        results = photon.search_cities(query)
    return JsonResponse({'results': results})
