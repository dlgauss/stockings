"""Main Moldovan towns, searched instantly in the order form and in Russian too.

Photon (see photon.py) covers every village, but only in Latin spelling; this list lets
"Бельцы" find Bălți. Coordinates come from Photon and steer the street search.
The first POPULAR_COUNT are shown before the customer types anything.
"""

from typing import NamedTuple


class City(NamedTuple):
    ro: str
    ru: str
    district: str
    lat: float
    lon: float


POPULAR_COUNT = 8

CITIES = [
    City('Chișinău', 'Кишинёв', 'Municipiul Chișinău', 47.02451, 28.83229),
    City('Bălți', 'Бельцы', 'Municipiul Bălți', 47.7624, 27.9286),
    City('Cahul', 'Кагул', 'Raionul Cahul', 45.90441, 28.19466),
    City('Orhei', 'Орхей', 'Raionul Orhei', 47.37823, 28.82468),
    City('Ungheni', 'Унгены', 'Raionul Ungheni', 47.206, 27.79892),
    City('Comrat', 'Комрат', 'Raionul Comrat', 46.30112, 28.65588),
    City('Soroca', 'Сороки', 'Raionul Soroca', 48.15427, 28.28835),
    City('Hîncești', 'Хынчешты', 'Raionul Hîncești', 46.82824, 28.58892),
    City('Edineț', 'Единец', 'Raionul Edineț', 48.16843, 27.29848),
    City('Strășeni', 'Стрэшень', 'Raionul Strășeni', 47.14744, 28.61502),
    City('Căușeni', 'Кэушень', 'Raionul Căușeni', 46.64954, 29.40677),
    City('Drochia', 'Дрокия', 'Raionul Drochia', 48.03181, 27.81572),
    City('Florești', 'Флорешты', 'Raionul Florești', 47.89383, 28.29965),
    City('Ialoveni', 'Яловены', 'Raionul Ialoveni', 46.94376, 28.77672),
    City('Fălești', 'Фалешты', 'Raionul Fălești', 47.57351, 27.7068),
    City('Sîngerei', 'Сынжерей', 'Raionul Sîngerei', 47.63609, 28.14554),
    City('Anenii Noi', 'Анений Ной', 'Raionul Anenii Noi', 46.87885, 29.2291),
    City('Criuleni', 'Криуляны', 'Raionul Criuleni', 47.21327, 29.15995),
    City('Nisporeni', 'Ниспорены', 'Raionul Nisporeni', 47.07758, 28.17784),
    City('Călărași', 'Кэлэрашь', 'Raionul Călărași', 47.25193, 28.3178),
    City('Rezina', 'Резина', 'Raionul Rezina', 47.74892, 28.95657),
    City('Telenești', 'Теленешты', 'Raionul Telenești', 47.5031, 28.36383),
    City('Șoldănești', 'Шолдэнешты', 'Raionul Șoldănești', 47.81356, 28.79323),
    City('Glodeni', 'Глодяны', 'Raionul Glodeni', 47.7744, 27.50441),
    City('Rîșcani', 'Рышканы', 'Raionul Rîșcani', 47.9536, 27.55145),
    City('Briceni', 'Бричаны', 'Raionul Briceni', 48.36133, 27.0849),
    City('Ocnița', 'Окница', 'Raionul Ocnița', 48.41033, 27.47882),
    City('Dondușeni', 'Дондюшаны', 'Raionul Dondușeni', 48.24188, 27.60705),
    City('Ceadîr-Lunga', 'Чадыр-Лунга', 'Raionul Ceadîr-Lunga', 46.05723, 28.825),
    City('Vulcănești', 'Вулкэнешть', 'Raionul Vulcănești', 45.6824, 28.40221),
    City('Taraclia', 'Тараклия', 'Raionul Taraclia', 45.89798, 28.66871),
    City('Basarabeasca', 'Басарабяска', 'Raionul Basarabeasca', 46.33249, 28.97609),
    City('Cimișlia', 'Чимишлия', 'Raionul Cimișlia', 46.52148, 28.7833),
    City('Leova', 'Леова', 'Raionul Leova', 46.48063, 28.25633),
    City('Cantemir', 'Кантемир', 'Raionul Cantemir', 46.2775, 28.2005),
    City('Ștefan Vodă', 'Штефан-Водэ', 'Raionul Ștefan Vodă', 46.51561, 29.66211),
    City('Durlești', 'Дурлешты', 'Municipiul Chișinău', 47.02283, 28.76417),
    City('Codru', 'Кодру', 'Municipiul Chișinău', 46.96893, 28.82767),
    City('Cricova', 'Крикова', 'Municipiul Chișinău', 47.13695, 28.86181),
    City('Sîngera', 'Сынжера', 'Municipiul Chișinău', 46.91401, 28.97254),
    City('Vadul lui Vodă', 'Вадул-луй-Водэ', 'Municipiul Chișinău', 47.08785, 29.07979),
    City('Otaci', 'Отачь', 'Raionul Ocnița', 48.4376, 27.79167),
    City('Cornești', 'Корнешты', 'Raionul Ungheni', 47.35649, 28.00916),
]


def options(lang):
    """The list for the order form's city dropdown, in the page's language.

    The value is always the Romanian name, so orders read the same in the admin.
    In Russian the hint shows that Romanian name, so the customer knows what gets filled in.
    """
    return [
        {
            'value': city.ro,
            'label': city.ru if lang == 'ru' else city.ro,
            'hint': city.ro if lang == 'ru' else city.district,
            'search': f'{city.ro} {city.ru}',
            'lat': city.lat,
            'lon': city.lon,
        }
        for city in CITIES
    ]
