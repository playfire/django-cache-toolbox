from django.test import TestCase

from .models import Foo

class CachedGetTest(TestCase):
    def test_cached_get(self):
        first_object = Foo.objects.create(bar='bees')

        # Populate the cache
        Foo.get_cached(first_object.pk)

        # Get from the cache
        cached_object = Foo.get_cached(first_object.pk)

        self.assertEqual(first_object.bar, cached_object.bar)
