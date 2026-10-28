from django.contrib import admin
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import LandingSettings, LegalPage, Order, Review, Size


def _photo_preview(field_name, url_attr):
    """The default photo, shown while nothing is uploaded (an upload has its own preview)."""
    @display(description=_('Default photo'))
    def preview(self, obj):
        if getattr(obj, field_name):
            return _('Replaced by the uploaded photo above.')
        return format_html(
            '<img src="{}" style="max-height:220px;max-width:100%;border-radius:10px">',
            getattr(obj, url_attr),
        )
    return preview


@admin.register(LandingSettings)
class LandingSettingsAdmin(ModelAdmin):
    readonly_fields = ['hero_preview', 'inside_preview', 'detail_1_preview', 'detail_2_preview']
    fieldsets = [
        (_('Photos'), {
            'classes': ['tab'],
            'description': _('Upload a photo to replace the one on the page. '
                             'Clear the field to go back to the default photo.'),
            'fields': [
                ('hero_photo', 'hero_preview'),
                ('inside_photo', 'inside_preview'),
                ('detail_photo_1', 'detail_1_preview'),
                ('detail_photo_2', 'detail_2_preview'),
            ],
        }),
        (_('Price'), {
            'classes': ['tab'],
            'fields': [
                ('price', 'old_price'),
                ('currency_ro', 'currency_ru'),
                'promo_until',
            ],
        }),
        (_('Social proof'), {
            'classes': ['tab'],
            'fields': ['orders_count', 'recommend_percent'],
        }),
        (_('Specs'), {
            'classes': ['tab'],
            'fields': [
                ('composition_ro', 'composition_ru'),
                ('size_range_ro', 'size_range_ru'),
                ('care_ro', 'care_ru'),
                ('country_ro', 'country_ru'),
            ],
        }),
        (_('Delivery'), {
            'classes': ['tab'],
            'fields': [
                ('delivery_area_ro', 'delivery_area_ru'),
                ('delivery_time_ro', 'delivery_time_ru'),
                'cash_on_delivery',
            ],
        }),
        (_('Contacts'), {
            'classes': ['tab'],
            'fields': [
                ('company_name', 'company_details'),
                ('phone', 'email'),
                'working_hours',
            ],
        }),
    ]

    hero_preview = _photo_preview('hero_photo', 'hero_url')
    inside_preview = _photo_preview('inside_photo', 'inside_url')
    detail_1_preview = _photo_preview('detail_photo_1', 'detail_1_url')
    detail_2_preview = _photo_preview('detail_photo_2', 'detail_2_url')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # A single record: skip the list and open it straight away.
        obj = LandingSettings.load()
        return redirect('admin:landing_landingsettings_change', obj.pk)


@admin.register(Size)
class SizeAdmin(ModelAdmin):
    list_display = ['label', 'position', 'is_active']
    list_editable = ['position', 'is_active']


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ['preview', 'caption_ro', 'position', 'is_active']
    list_editable = ['position', 'is_active']
    fields = ['image', ('caption_ro', 'caption_ru'), ('position', 'is_active')]

    @display(description=_('Image'))
    def preview(self, obj):
        return format_html('<img src="{}" style="height:60px;border-radius:6px">', obj.image.url)


@admin.register(LegalPage)
class LegalPageAdmin(ModelAdmin):
    list_display = ['kind']
    fields = ['kind', 'body_ro', 'body_ru']


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = [
        'id', 'created_at', 'name', 'phone', 'quantity', 'size', 'city',
        'total_display', 'language', 'status_display',
    ]
    list_display_links = ['id', 'name']
    list_filter = ['status', 'language', 'created_at']
    search_fields = ['name', 'phone', 'city', 'address']
    readonly_fields = ['unit_price', 'currency', 'language', 'created_at', 'updated_at']
    fieldsets = [
        (None, {'fields': ['status', 'note']}),
        (_('Customer'), {'fields': [('name', 'phone'), ('city', 'address')]}),
        (_('Order details'), {
            'fields': [
                ('quantity', 'size'),
                ('unit_price', 'currency'),
                ('language', 'created_at', 'updated_at'),
            ],
        }),
    ]

    @display(description=_('Total'), ordering='unit_price')
    def total_display(self, obj):
        if obj.total is None:
            return '—'
        return f'{obj.total:.2f} {obj.currency}'

    @display(
        description=_('Status'),
        ordering='status',
        label={
            Order.Status.NEW: 'info',
            Order.Status.CONFIRMED: 'warning',
            Order.Status.SHIPPED: 'success',
            Order.Status.CANCELLED: 'danger',
        },
    )
    def status_display(self, obj):
        return obj.status, obj.get_status_display()
