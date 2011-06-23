from django.conf import settings

# Default cache timeout
CACHE_RELATION_DEFAULT_DURATION = getattr(
    settings,
    'CACHE_RELATION_DEFAULT_DURATION',
    60 * 60 * 24 * 3,
)
