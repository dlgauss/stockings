import re

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Order


def _suggest_attrs(kind, placeholder):
    """Attributes for an input that shows city/street suggestions (see static/landing/js/landing.js)."""
    return {
        'class': 'input combo-input',
        'placeholder': placeholder,
        'autocomplete': 'off',
        'role': 'combobox',
        'aria-autocomplete': 'list',
        'aria-expanded': 'false',
        'aria-controls': f'suggest-{kind}',
        'data-suggest': kind,
    }


class OrderForm(forms.ModelForm):
    # Hidden from people with CSS; bots that fill every field get caught by it.
    website = forms.CharField(required=False)

    class Meta:
        model = Order
        fields = ['name', 'phone', 'quantity', 'size', 'city', 'address']
        labels = {
            'name': _('Your name'),
            'phone': _('Phone'),
            'quantity': _('Quantity'),
            'size': _('Size'),
            'city': _('City or village'),
            'address': _('Street and house number'),
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input', 'autocomplete': 'name', 'placeholder': _('Name'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input', 'type': 'tel', 'autocomplete': 'tel',
                'placeholder': '+373 000 00 000',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'input', 'inputmode': 'numeric', 'min': 1, 'max': 20,
            }),
            'city': forms.TextInput(attrs=_suggest_attrs('city', _('E.g. Chișinău'))),
            'address': forms.TextInput(attrs=_suggest_attrs('street', _('E.g. str. Mihai Viteazul 15'))),
        }

    def __init__(self, *args, sizes=(), **kwargs):
        super().__init__(*args, **kwargs)
        if sizes:
            self.fields['size'] = forms.ChoiceField(
                label=self.fields['size'].label,
                choices=[('', '—')] + [(s, s) for s in sizes],
                widget=forms.Select(attrs={'class': 'input'}),
            )
        else:
            del self.fields['size']

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D', '', phone)
        if not 6 <= len(digits) <= 15:
            raise forms.ValidationError(_('Enter a valid phone number.'))
        return phone
