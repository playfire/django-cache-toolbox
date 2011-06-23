from django.conf import settings

# Default cache timeout
CACHE_RELATION_DEFAULT_TIMEOUT = getattr(
    settings,
    'CACHE_RELATION_DEFAULT_TIMEOUT',
    60 * 60 * 24 * 3,
)
