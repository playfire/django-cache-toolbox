from unittest import skip

from django.test import TestCase

from .models import Foo, Bazz

class CachedRelationTest(TestCase):
    @skip("Currently broken")
    def test_cached_relation(self):
        foo = Foo.objects.create(bar='bees')

        Bazz.objects.create(foo=foo, value=10)

        # Populate the cache
        Foo.objects.get(pk=foo.pk).bazz_cache

        # Get from the cache
        cached_object = Foo.objects.get(pk=foo.pk).bazz_cache

        self.assertEqual(cached_object.value, 10)
