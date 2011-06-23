from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import User
from django.contrib.auth.middleware import AuthenticationMiddleware

from .models import cache_model


class CacheBackedAuthenticationMiddleware(AuthenticationMiddleware):
    def __init__(self):
        cache_model(User)

    def process_request(self, request):
        try:
            # Try and construct a User instance from data stored in the cache
            user_id = request.session[SESSION_KEY]

            request.user = User.get_cached(user_id)
        except:
            # Fallback to constructing the User from the database.
            super(CacheBackedAuthenticationMiddleware, self).process_request(request)
