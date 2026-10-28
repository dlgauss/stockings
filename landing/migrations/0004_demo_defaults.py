"""Demo content for the client presentation, so the page is complete right after deploy.

Only empty values are filled in: anything already set in the admin is left as it is.
Everything here is meant to be replaced in the admin with the real data.
"""

import datetime
from decimal import Decimal

from django.db import migrations

SETTINGS = {
    'price': Decimal('499'),
    'old_price': Decimal('1000'),
    'promo_until': datetime.date(2026, 12, 31),
    'orders_count': 1250,
    'recommend_percent': 96,
    'composition_ro': '80% cașmir, 20% poliamidă',
    'composition_ru': '80% кашемир, 20% полиамид',
    'size_range_ro': '36–45',
    'size_range_ru': '36–45',
    'care_ro': 'Spălare delicată la 30°C',
    'care_ru': 'Деликатная стирка при 30°C',
    'country_ro': 'China',
    'country_ru': 'Китай',
    'delivery_area_ro': 'în toată Moldova',
    'delivery_area_ru': 'по всей Молдове',
    'delivery_time_ro': '1–3 zile',
    'delivery_time_ru': '1–3 дня',
    'company_name': 'SRL Cashmere Termo',
    'company_details': 'IDNO 1000000000000, mun. Chișinău',
    'phone': '+373 60 000 000',
    'email': 'info@stockings.talkboard.chat',
    'working_hours': '9:00–20:00',
}

SIZES = ['36–38', '39–42', '43–45']

LEGAL_PAGES = {
    'privacy': (
        'Datele tale (nume, telefon, adresă) le folosim doar pentru a procesa și livra comanda. '
        'Nu le transmitem terților, cu excepția serviciului de livrare.\n\n'
        'Poți cere oricând ștergerea datelor scriindu-ne pe email.',
        'Ваши данные (имя, телефон, адрес) мы используем только для обработки и доставки заказа. '
        'Мы не передаём их третьим лицам, кроме службы доставки.\n\n'
        'Вы можете в любой момент попросить удалить данные, написав нам на email.',
    ),
    'terms': (
        'Comanda se confirmă telefonic de un manager. Prețul valabil este cel afișat '
        'în momentul comenzii. Plata se face la livrare.',
        'Заказ подтверждает менеджер по телефону. Действует цена, указанная '
        'в момент заказа. Оплата при получении.',
    ),
    'returns': (
        'Poți returna setul în 14 zile de la primire, dacă produsul nu a fost purtat '
        'și este în ambalajul original. Banii se returnează în 3 zile lucrătoare.',
        'Вы можете вернуть набор в течение 14 дней после получения, если товар не был в носке '
        'и сохранена оригинальная упаковка. Деньги возвращаются в течение 3 рабочих дней.',
    ),
}


def add_demo_content(apps, schema_editor):
    LandingSettings = apps.get_model('landing', 'LandingSettings')
    Size = apps.get_model('landing', 'Size')
    LegalPage = apps.get_model('landing', 'LegalPage')

    content, _created = LandingSettings.objects.get_or_create(pk=1)
    for field, value in SETTINGS.items():
        if getattr(content, field) in (None, ''):
            setattr(content, field, value)
    content.save()

    if not Size.objects.exists():
        Size.objects.bulk_create(
            Size(label=label, position=position) for position, label in enumerate(SIZES)
        )

    for kind, (body_ro, body_ru) in LEGAL_PAGES.items():
        page, _created = LegalPage.objects.get_or_create(kind=kind)
        if not page.body_ro:
            page.body_ro = body_ro
        if not page.body_ru:
            page.body_ru = body_ru
        page.save()


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0003_translated_labels'),
    ]

    operations = [
        migrations.RunPython(add_demo_content, migrations.RunPython.noop),
    ]
