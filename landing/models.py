from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.templatetags.static import static
from django.utils.translation import get_language, gettext_lazy as _


class Translated:
    """Reads `<name>_<lang>` for the active language, falling back to Romanian."""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        lang = (get_language() or settings.LANGUAGE_CODE)[:2]
        return getattr(obj, f'{self.name}_{lang}', '') or getattr(obj, f'{self.name}_ro')


class PhotoURL:
    """URL of an uploaded photo, or of the bundled default photo when none is uploaded."""

    def __init__(self, field_name, default):
        self.field_name = field_name
        self.default = default

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        image = getattr(obj, self.field_name)
        return image.url if image else static(self.default)


class LandingSettings(models.Model):
    """Values for the placeholders on the landing page. There is only one row (pk=1)."""

    hero_photo = models.ImageField(
        _('main photo'), upload_to='landing/', blank=True,
        help_text=_('Top of the page, next to the title. Portrait 3:4, e.g. 1200×1600. '
                    'Empty: the default photo is shown.'),
    )
    hero_url = PhotoURL('hero_photo', 'landing/img/hero.jpg')
    inside_photo = models.ImageField(
        _('"what\'s inside" photo'), upload_to='landing/', blank=True,
        help_text=_('Next to the list of colours. Portrait 4:5, e.g. 1200×1500.'),
    )
    inside_url = PhotoURL('inside_photo', 'landing/img/inside.jpg')
    detail_photo_1 = models.ImageField(
        _('description photo 1'), upload_to='landing/', blank=True,
        help_text=_('Description section, left. Landscape 4:3, e.g. 1200×900.'),
    )
    detail_1_url = PhotoURL('detail_photo_1', 'landing/img/tag.jpg')
    detail_photo_2 = models.ImageField(
        _('description photo 2'), upload_to='landing/', blank=True,
        help_text=_('Description section, right. Landscape 4:3, e.g. 1200×900.'),
    )
    detail_2_url = PhotoURL('detail_photo_2', 'landing/img/sock.jpg')

    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, null=True, blank=True)
    old_price = models.DecimalField(
        _('old price'), max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_('Shown crossed out. The discount badge is calculated from the two prices.'),
    )
    currency_ro = models.CharField(_('currency (RO)'), max_length=20, default='lei')
    currency_ru = models.CharField(_('currency (RU)'), max_length=20, default='лей')
    currency = Translated()
    promo_until = models.DateField(
        _('promo ends on'), null=True, blank=True,
        help_text=_('Leave empty to hide the "offer valid until" line.'),
    )

    orders_count = models.PositiveIntegerField(
        _('people who ordered'), null=True, blank=True,
        help_text=_('The number in "N people have already ordered this set".'),
    )
    recommend_percent = models.PositiveSmallIntegerField(
        _('recommend, %'), null=True, blank=True, validators=[MaxValueValidator(100)],
        help_text=_('The number in "XX% of buyers recommend the set".'),
    )

    composition_ro = models.CharField(_('composition (RO)'), max_length=255, blank=True)
    composition_ru = models.CharField(_('composition (RU)'), max_length=255, blank=True)
    composition = Translated()
    size_range_ro = models.CharField(_('size range (RO)'), max_length=255, blank=True)
    size_range_ru = models.CharField(_('size range (RU)'), max_length=255, blank=True)
    size_range = Translated()
    care_ro = models.CharField(_('care (RO)'), max_length=255, blank=True)
    care_ru = models.CharField(_('care (RU)'), max_length=255, blank=True)
    care = Translated()
    country_ro = models.CharField(_('country of origin (RO)'), max_length=255, blank=True)
    country_ru = models.CharField(_('country of origin (RU)'), max_length=255, blank=True)
    country = Translated()

    delivery_area_ro = models.CharField(
        _('delivery area (RO)'), max_length=255, blank=True,
        help_text=_('With the preposition, e.g. "în toată Moldova".'),
    )
    delivery_area_ru = models.CharField(
        _('delivery area (RU)'), max_length=255, blank=True,
        help_text=_('With the preposition, e.g. "по всей Молдове".'),
    )
    delivery_area = Translated()
    delivery_time_ro = models.CharField(
        _('delivery time (RO)'), max_length=255, blank=True, help_text=_('E.g. "1–3 zile".'),
    )
    delivery_time_ru = models.CharField(
        _('delivery time (RU)'), max_length=255, blank=True, help_text=_('E.g. "1–3 дня".'),
    )
    delivery_time = Translated()
    cash_on_delivery = models.BooleanField(
        _('cash on delivery'), default=True, help_text=_('Shows the "pay on delivery" step.'),
    )

    company_name = models.CharField(_('company name'), max_length=255, blank=True)
    company_details = models.CharField(
        _('company details'), max_length=255, blank=True,
        help_text=_('Registration number, address, etc.'),
    )
    phone = models.CharField(_('phone'), max_length=50, blank=True)
    email = models.EmailField(_('email'), blank=True)
    working_hours = models.CharField(
        _('working hours'), max_length=100, blank=True, help_text=_('E.g. "9:00–20:00".'),
    )

    class Meta:
        verbose_name = _('landing settings')
        verbose_name_plural = _('landing settings')

    def __str__(self):
        return str(_('Landing settings'))

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def discount_percent(self):
        if self.price and self.old_price and self.old_price > self.price:
            return round((self.old_price - self.price) / self.old_price * 100)
        return None


class Size(models.Model):
    label = models.CharField(_('label'), max_length=50, help_text=_('E.g. "36–38".'))
    position = models.PositiveSmallIntegerField(_('position'), default=0)
    is_active = models.BooleanField(_('shown in the form'), default=True)

    class Meta:
        ordering = ['position', 'id']
        verbose_name = _('size')
        verbose_name_plural = _('sizes')

    def __str__(self):
        return self.label


class Review(models.Model):
    image = models.ImageField(
        _('image'), upload_to='reviews/', help_text=_('Photo or chat screenshot.'),
    )
    caption_ro = models.CharField(_('caption (RO)'), max_length=255, blank=True)
    caption_ru = models.CharField(_('caption (RU)'), max_length=255, blank=True)
    caption = Translated()
    position = models.PositiveSmallIntegerField(_('position'), default=0)
    is_active = models.BooleanField(_('shown on the page'), default=True)

    class Meta:
        ordering = ['position', 'id']
        verbose_name = _('review')
        verbose_name_plural = _('reviews')

    def __str__(self):
        return self.caption_ro or self.image.name


class LegalPage(models.Model):
    class Kind(models.TextChoices):
        PRIVACY = 'privacy', _('Privacy policy')
        TERMS = 'terms', _('Terms of use')
        RETURNS = 'returns', _('Return policy')

    kind = models.CharField(_('page'), max_length=20, choices=Kind.choices, unique=True)
    body_ro = models.TextField(_('text (RO)'), blank=True)
    body_ru = models.TextField(_('text (RU)'), blank=True)
    body = Translated()

    class Meta:
        ordering = ['kind']
        verbose_name = _('legal page')
        verbose_name_plural = _('legal pages')

    def __str__(self):
        return str(self.get_kind_display())


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        CONFIRMED = 'confirmed', _('Confirmed')
        SHIPPED = 'shipped', _('Shipped')
        CANCELLED = 'cancelled', _('Cancelled')

    name = models.CharField(_('name'), max_length=100)
    phone = models.CharField(_('phone'), max_length=30)
    quantity = models.PositiveSmallIntegerField(
        _('quantity'), default=1, validators=[MinValueValidator(1), MaxValueValidator(20)],
    )
    size = models.CharField(_('size'), max_length=50, blank=True)
    city = models.CharField(_('city'), max_length=150)
    address = models.CharField(_('address'), max_length=255, blank=True)

    unit_price = models.DecimalField(
        _('unit price'), max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_('Price of one set at the moment of the order.'),
    )
    currency = models.CharField(_('currency'), max_length=20, blank=True)
    language = models.CharField(_('language'), max_length=2, choices=settings.LANGUAGES)

    status = models.CharField(
        _('status'), max_length=20, choices=Status.choices, default=Status.NEW,
    )
    note = models.TextField(_('manager note'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return f'#{self.pk} {self.name}'

    @property
    def total(self):
        if self.unit_price is None:
            return None
        return self.unit_price * self.quantity
