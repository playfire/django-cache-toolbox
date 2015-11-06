from django.test import TestCase

from .models import Foo

class CachedGetTest(TestCase):
    def setUp(self):
        self.foo = Foo.objects.create(bar='bees')
        self._populate_cache()

    def _populate_cache(self):
        Foo.get_cached(self.foo.pk)

    def test_cached_get(self):
        # Get from the cache
        cached_object = Foo.get_cached(self.foo.pk)

        self.assertEqual(self.foo.bar, cached_object.bar)

    def test_cache_invalidated_on_update(self):
        self.foo.bar = 'quux'
        self.foo.save()

        self._populate_cache()

        self.assertEqual(Foo.get_cached(self.foo.pk).bar, 'quux')

    def test_cache_invalidated_on_delete(self):
        self.foo.bar = 'quux'
        self.foo.delete()

        self._populate_cache()
