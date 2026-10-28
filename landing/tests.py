import io
import shutil
import tempfile
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .models import LandingSettings, LegalPage, Order, Size


class DemoContentTests(TestCase):
    """Migration 0004 fills a fresh database with demo content."""

    def test_fresh_database_has_demo_content(self):
        content = LandingSettings.load()
        self.assertEqual((content.price, content.old_price), (Decimal('499'), Decimal('1000')))
        self.assertEqual(content.discount_percent, 50)
        self.assertEqual(list(Size.objects.values_list('label', flat=True)), ['36–38', '39–42', '43–45'])
        self.assertEqual(LegalPage.objects.exclude(body_ro='').count(), 3)
        self.assertContains(self.client.get('/ru/'), '499 лей')


def clear_demo_content():
    LandingSettings.objects.all().delete()
    Size.objects.all().delete()
    LegalPage.objects.all().delete()


class LandingPageTests(TestCase):
    def setUp(self):
        clear_demo_content()
        content = LandingSettings.load()
        content.price = Decimal('349.00')
        content.old_price = Decimal('499.00')
        content.orders_count = 1250
        content.composition_ro = '80% cașmir'
        content.composition_ru = '80% кашемир'
        content.save()

    def test_root_redirects_to_a_language(self):
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='ru')
        self.assertRedirects(response, '/ru/')

    def test_page_shows_placeholders_in_each_language(self):
        ro = self.client.get('/ro/')
        self.assertContains(ro, 'Șosete termo din cașmir')
        self.assertContains(ro, '349 lei')
        self.assertContains(ro, '−30%')
        self.assertContains(ro, '80% cașmir')
        self.assertContains(ro, '1250 de persoane au comandat deja')

        ru = self.client.get('/ru/')
        self.assertContains(ru, 'Кашемировые термоноски')
        self.assertContains(ru, '349 лей')
        self.assertContains(ru, '80% кашемир')

    def test_empty_placeholders_are_hidden(self):
        content = LandingSettings.load()
        content.old_price = None
        content.save()
        response = self.client.get('/ro/')
        self.assertNotContains(response, 'class="badge"')
        self.assertNotContains(response, 'Țara de producție')

    def test_order_is_saved_with_price_snapshot(self):
        Size.objects.create(label='39–42')
        response = self.client.post('/ru/', {
            'name': 'Ion', 'phone': '+373 69 123 456', 'quantity': 2, 'size': '39–42',
            'city': 'Chișinău', 'address': 'Strada Mihai Viteazul 15',
        })
        self.assertRedirects(response, '/ru/thank-you/', fetch_redirect_response=False)
        order = Order.objects.get()
        self.assertEqual(order.language, 'ru')
        self.assertEqual(order.currency, 'лей')
        self.assertEqual(order.total, Decimal('698.00'))
        self.assertEqual(order.status, Order.Status.NEW)

        thanks = self.client.get('/ru/thank-you/')
        self.assertContains(thanks, f'Ваш заказ № {order.pk} принят.')

    def test_invalid_order_shows_errors(self):
        response = self.client.post('/ro/', {'name': '', 'phone': '12', 'quantity': 1, 'city': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Introdu un număr de telefon valid.')
        self.assertFalse(Order.objects.exists())

    def test_honeypot_order_is_not_saved(self):
        response = self.client.post('/ro/', {
            'name': 'Bot', 'phone': '+37369123456', 'quantity': 1, 'city': 'X',
            'website': 'http://spam.example',
        })
        self.assertRedirects(response, '/ro/thank-you/')
        self.assertFalse(Order.objects.exists())

    def test_legal_page_link_appears_only_with_text(self):
        self.assertNotContains(self.client.get('/ro/'), '/ro/privacy/')
        LegalPage.objects.create(kind='privacy', body_ro='Text', body_ru='Текст')
        self.assertContains(self.client.get('/ro/'), '/ro/privacy/')
        self.assertContains(self.client.get('/ru/privacy/'), 'Текст')
        self.assertEqual(self.client.get('/ro/terms/').status_code, 404)


class PhotoTests(TestCase):
    def setUp(self):
        clear_demo_content()
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)

    def test_default_photos_until_one_is_uploaded(self):
        response = self.client.get('/ro/')
        self.assertContains(response, '/static/landing/img/hero.jpg')

        buffer = io.BytesIO()
        Image.new('RGB', (30, 40), 'white').save(buffer, 'JPEG')
        with override_settings(MEDIA_ROOT=self.media):
            content = LandingSettings.load()
            content.hero_photo = SimpleUploadedFile('new.jpg', buffer.getvalue(), 'image/jpeg')
            content.save()
            response = self.client.get('/ro/')
        self.assertContains(response, '/media/landing/new')
        self.assertNotContains(response, '/static/landing/img/hero.jpg')
        self.assertContains(response, '/static/landing/img/inside.jpg')


class AddressSuggestTests(TestCase):
    CITY = {
        'geometry': {'coordinates': [27.93, 47.76]},
        'properties': {'countrycode': 'MD', 'osm_key': 'place', 'osm_value': 'city', 'name': 'Bălți'},
    }

    def street(self, name, lon, lat, city):
        return {
            'geometry': {'coordinates': [lon, lat]},
            'properties': {'countrycode': 'MD', 'name': name, 'city': city},
        }

    @mock.patch('landing.photon._fetch')
    def test_cities(self, fetch):
        fetch.return_value = [self.CITY, self.CITY]
        response = self.client.get('/api/address/', {'q': 'balti'})
        self.assertEqual(response.json()['results'], [
            {'value': 'Bălți', 'hint': '', 'lat': 47.76, 'lon': 27.93},
        ])

    @mock.patch('landing.photon._fetch')
    def test_streets_keep_house_number_and_stay_in_city(self, fetch):
        fetch.return_value = [
            self.street('Strada Mihai Viteazul', 28.83, 47.02, 'Municipiul Chișinău'),
            self.street('Strada Mihai Viteazul', 28.84, 47.03, 'Municipiul Chișinău'),  # segment
            self.street('Strada Mihai Viteazul', 28.78, 46.94, 'Ialoveni'),  # nearby town
        ]
        response = self.client.get('/api/address/', {
            'q': 'mihai viteazul 15', 'kind': 'street', 'city': 'Chisinau',
            'lat': 47.02, 'lon': 28.83,
        })
        self.assertEqual(response.json()['results'], [{
            'value': 'Strada Mihai Viteazul 15',
            'hint': 'Municipiul Chișinău',
        }])
        self.assertEqual(fetch.call_args.args[0]['q'], 'mihai viteazul Chisinau')

    @mock.patch('landing.photon._fetch')
    def test_streets_fall_back_to_distance_for_unknown_city(self, fetch):
        fetch.return_value = [
            self.street('Strada Livezilor', 28.83, 47.02, 'Municipiul Chișinău'),
            self.street('Strada Livezilor', 27.93, 47.76, 'Bălți'),
        ]
        response = self.client.get('/api/address/', {
            'q': 'livezilor', 'kind': 'street', 'city': 'Satul Meu', 'lat': 47.03, 'lon': 28.84,
        })
        self.assertEqual(
            [r['hint'] for r in response.json()['results']],
            ['Municipiul Chișinău'],
        )

    def test_page_embeds_city_list_in_page_language(self):
        response = self.client.get('/ru/')
        cities = response.context['combo_data']['cities']
        balti = next(c for c in cities if c['value'] == 'Bălți')
        self.assertEqual((balti['label'], balti['hint']), ('Бельцы', 'Bălți'))
        self.assertContains(response, 'id="combo-data"')
        self.assertEqual(response.context['combo_data']['text']['popular'], 'Популярные города')

    def test_short_query_returns_nothing(self):
        self.assertEqual(self.client.get('/api/address/', {'q': 'a'}).json(), {'results': []})


class AdminTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser('admin', 'a@example.com', 'pw')
        self.client.force_login(user)

    def test_settings_list_opens_the_single_record(self):
        response = self.client.get('/admin/landing/landingsettings/')
        self.assertRedirects(response, '/admin/landing/landingsettings/1/change/')

    def test_admin_pages_render(self):
        Order.objects.create(name='Ion', phone='069123456', city='Chișinău', language='ro')
        for url in [
            '/admin/landing/landingsettings/1/change/',
            '/admin/landing/order/',
            '/admin/landing/order/1/change/',
            '/admin/landing/size/',
            '/admin/landing/review/',
            '/admin/landing/legalpage/',
        ]:
            LandingSettings.load()
            self.assertEqual(self.client.get(url).status_code, 200, url)


@override_settings(DEBUG=False)
class NotFoundPageTests(TestCase):
    def test_404_uses_site_design_in_page_language(self):
        response = self.client.get('/ru/no-such-page/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Страница не найдена', status_code=404)
        self.assertContains(response, 'href="/ru/"', status_code=404)
        # The language switch leads to the main page, not to another missing page.
        self.assertContains(response, '<a href="/ro/" hreflang="ro"', status_code=404)

        response = self.client.get('/ro/no-such-page/')
        self.assertContains(response, 'Pagina nu a fost găsită', status_code=404)


class AdminLanguageTests(TestCase):
    def test_admin_labels_follow_browser_language(self):
        user = get_user_model().objects.create_superuser('admin', 'a@example.com', 'pw')
        self.client.force_login(user)
        LandingSettings.load()
        response = self.client.get(
            '/admin/landing/landingsettings/1/change/', HTTP_ACCEPT_LANGUAGE='ro',
        )
        self.assertContains(response, 'Fotografii')
        self.assertContains(response, 'Preț vechi')
        response = self.client.get('/admin/landing/order/', HTTP_ACCEPT_LANGUAGE='ru')
        self.assertContains(response, 'Заказы')
