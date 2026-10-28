"""City and street suggestions for the order form, from Photon (OpenStreetMap).

https://photon.komoot.io — free, no API key, fair use. Results are limited to Moldova.
Photon only matches Latin spelling (Bălți / Balti), not Cyrillic.
"""

import hashlib
import json
import logging
import math
import re
import unicodedata
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

logger = logging.getLogger(__name__)

PHOTON_URL = 'https://photon.komoot.io/api/'
MOLDOVA_BBOX = '26.6,45.4,30.2,48.5'
COUNTRY_CODE = 'MD'
SETTLEMENT_TYPES = {'city', 'town', 'village', 'hamlet'}
STREET_RADIUS_KM = 15
MAX_RESULTS = 6
CACHE_SECONDS = 60 * 60 * 24

HOUSE_NUMBER_RE = re.compile(r'^(?P<street>.*?)[\s,]+(?P<number>\d+[\w/-]*)$')


def _normalize(text):
    text = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).casefold().strip()


def _distance_km(lat1, lon1, lat2, lon2):
    # Equirectangular approximation: accurate enough at the scale of one city.
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    y = math.radians(lat2 - lat1)
    return math.hypot(x, y) * 6371


def _fetch(params):
    query = _normalize(urlencode(sorted(params.items())))
    key = 'photon:' + hashlib.sha256(query.encode()).hexdigest()
    features = cache.get(key)
    if features is not None:
        return features
    request = Request(
        f'{PHOTON_URL}?{urlencode(params)}',
        headers={'User-Agent': 'cashmere-termo-landing/1.0'},
    )
    try:
        with urlopen(request, timeout=4) as response:
            features = json.load(response).get('features', [])
    except (URLError, TimeoutError, ValueError) as exc:
        logger.warning('Photon lookup failed: %s', exc)
        return []
    features = [f for f in features if f['properties'].get('countrycode') == COUNTRY_CODE]
    cache.set(key, features, CACHE_SECONDS)
    return features


def search_cities(query):
    features = _fetch({'q': query, 'limit': 15, 'bbox': MOLDOVA_BBOX, 'osm_tag': 'place'})
    results, seen = [], set()
    for feature in features:
        props = feature['properties']
        if props.get('osm_value') not in SETTLEMENT_TYPES:
            continue
        name, county = props.get('name', ''), props.get('county', '')
        dedupe_key = (_normalize(name), _normalize(county))
        if not name or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        lon, lat = feature['geometry']['coordinates']
        results.append({'value': name, 'hint': county, 'lat': lat, 'lon': lon})
    return results[:MAX_RESULTS]


def search_streets(query, city='', lat=None, lon=None):
    """Streets in the chosen city. A trailing house number is kept and added back.

    The city name goes into the query, because Photon ranks a big city's streets above
    those of a nearby village. Streets whose city matches are shown; if none do (the city
    was typed freely), streets within STREET_RADIUS_KM of the city's coordinates are.
    """
    match = HOUSE_NUMBER_RE.match(query)
    street_query, number = (match['street'], match['number']) if match else (query, '')
    params = {
        'q': f'{street_query} {city}'.strip(),
        'limit': 20,
        'bbox': MOLDOVA_BBOX,
        'osm_tag': 'highway',
    }
    if lat is not None and lon is not None:
        params.update(lat=lat, lon=lon)

    in_city, nearby, seen = [], [], set()
    for feature in _fetch(params):
        props = feature['properties']
        name, place = props.get('name', ''), props.get('city') or props.get('district') or ''
        dedupe_key = (_normalize(name), _normalize(place))
        if not name or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        value = f'{name} {number}' if number else name
        result = {'value': value, 'hint': place}

        if city and _normalize(city) in _normalize(place):
            in_city.append(result)
        elif lat is not None and lon is not None:
            f_lon, f_lat = feature['geometry']['coordinates']
            if _distance_km(lat, lon, f_lat, f_lon) <= STREET_RADIUS_KM:
                nearby.append(result)
        elif not city:
            nearby.append(result)
    return (in_city or nearby)[:MAX_RESULTS]
