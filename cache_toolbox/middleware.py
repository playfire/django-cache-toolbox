"""
Cache-backed ``AuthenticationMiddleware``
-----------------------------------------

``CacheBackedAuthenticationMiddleware`` is an
``django.contrib.auth.middleware.AuthenticationMiddleware`` replacement to
avoid querying the database for a ``User`` instance in each request.

Whilst the built-in ``AuthenticationMiddleware`` mechanism will only obtain the
``User`` instance when it is required, the vast majority of sites will do so on
every page to render "Logged in as 'X'" text as well to evaluate the result of
``user.is_authenticated()`` and ``user.is_superuser`` to provide conditional
functionality.

This middleware eliminates the cost of retrieving this ``User`` instance by
caching it using the ``cache_toolbox`` instance caching mechanisms.

Depending on your average number of queries per page, saving one query per
request can---in aggregate---reduce load on your database. In addition,
avoiding the database entirely for pages can avoid incurring any connection
latency in your environment, resulting in faster page loads for your users.

Saving this data in the cache can also be used as a way of authenticating users
in systems outside of Django that should not access your database.  For
example, a "maintenance mode" page would be able to render a personalised
message without touching the database at all but rather authenticating via the
cache.

``CacheBackedAuthenticationMiddleware`` is ``AUTHENTICATION_BACKENDS`` agnostic.

Implementation
~~~~~~~~~~~~~~

The cache and session backends are still accessed on each request - we are
simply assuming that they are cheaper (or otherwise more preferable) to access
than your database. (In the future, signed cookies may allow us to avoid this
lookup altogether -- whilst we could not safely save ``User.password`` in a
cookie, we could use delayed loading to pull it out when needed.)

Another alternative solution would be to store the attributes in the user's
session instead of in the cache. This would save the cache hit on every request
as all the relevant data would be pulled in one go from the session backend.
However, this has two main disadvantages:

 * Session keys are not deterministic -- after making changes to an
   ``auth_user`` row in the database, you cannot determine the user's session
   key to flush the now out-of-sync data (and doing so would log them out
   anyway).

 * Stores data per-session rather than per-user -- if a user logs in from
   multiple computers the data is duplicated in each session. This problem is
   compounded by most projects wishing to avoid expiring session data as long
   as possible (in addition to storing sessions in persistent stores).

Usage
~~~~~

To use, find ``MIDDLEWARE_CLASSES`` in your ``settings.py`` and replace::

    MIDDLEWARE_CLASSES = [
        ...
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        ...
    ]

with::

    MIDDLEWARE_CLASSES = [
        ...
        'cache_toolbox.middleware.CacheBackedAuthenticationMiddleware',
        ...
    ]

You should confirm you are using a ``SESSION_ENGINE`` that doesn't query the
database for each request. The built-in ``cached_db`` engine is the safest
choice for most environments but you may be happy with the trade-offs of the
``memcached`` backend - see the Django documentation for more details.

"""

from django.contrib.auth import SESSION_KEY
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware

from .model import cache_model


class CacheBackedAuthenticationMiddleware(AuthenticationMiddleware):
    def __init__(self, get_response):
        super(CacheBackedAuthenticationMiddleware, self).__init__(get_response)
        cache_model(get_user_model())

    def process_request(self, request):
        try:
            # Try and construct a User instance from data stored in the cache
            request.user = get_user_model().get_cached(
                int(request.session[SESSION_KEY])
            )
        except Exception:
            # Fallback to constructing the User from the database.
            super(CacheBackedAuthenticationMiddleware, self).process_request(request)
