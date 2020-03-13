from django.core.cache import cache
from django.test import TestCase

from .models import Foo, Bazz

class CachedRelationTest(TestCase):
    longMessage = True

    def setUp(self):
        # Ensure we start with a clear cache for each test, i.e. tests can use
        # the cache hygenically
        cache.clear()

    def test_cached_relation(self):
        foo = Foo.objects.create(bar='bees')

        Bazz.objects.create(foo=foo, value=10)

        # Populate the cache
        Foo.objects.get(pk=foo.pk).bazz_cache

        # Get from the cache
        cached_object = Foo.objects.get(pk=foo.pk).bazz_cache

        self.assertEqual(cached_object.value, 10)

        self.assertTrue(
            hasattr(foo, 'bazz'),
            "Foo should have 'bazz' attribute",
        )

        self.assertTrue(
            hasattr(foo, 'bazz_cache'),
            "Foo should have 'bazz_cache' attribute",
        )

    def test_cached_relation_not_present_hasattr(self):
        foo = Foo.objects.create(bar='bees_2')

        self.assertFalse(
            hasattr(foo, 'bazz_cache'),
            "Foo should not have 'bazz_cache' attribute (empty cache)",
        )

        self.assertFalse(
            hasattr(foo, 'bazz_cache'),
            "Foo should not have 'bazz_cache' attribute (warm cache; before natural access)",
        )

        # sanity check
        self.assertFalse(
            hasattr(foo, 'bazz'),
            "Foo should not have 'bazz' attribute",
        )

        self.assertFalse(
            hasattr(foo, 'bazz_cache'),
            "Foo should not have 'bazz_cache' attribute (warm cache; after natural access)",
        )

    def test_cached_relation_not_present_exception(self):
        foo = Foo.objects.create(bar='bees_3')

        with self.assertRaises(Bazz.DoesNotExist) as cm:
            foo.bazz_cache

        self.assertIsInstance(
            cm.exception,
            AttributeError,
            "Raised error must also be an AttributeError (we're expecting a 'RelatedObjectDoesNotExist')",
        )

    def test_cached_missing_relation_uses_select_related(self):
        foo = Foo.objects.create(bar='bees')

        with self.assertNumQueries(1):
            foo = Foo.objects.select_related('bazz').get(pk=foo.pk)

        with self.assertNumQueries(0):
            with self.assertRaises(Bazz.DoesNotExist):
                foo.bazz_cache

    def test_cached_missing_relation_cached_locally(self):
        # Django will cache on the instance that foo.bazz doesn't exist, just
        # the same as it would cache the Bazz instance if there was one. Mimic
        # that behaviour in order to have comparable querying behaviour.

        foo = Foo.objects.create(bar='bees')

        with self.assertNumQueries(1):
            foo = Foo.objects.get(pk=foo.pk)

        # Populate the (instance) cache
        with self.assertNumQueries(1):
            with self.assertRaises(Bazz.DoesNotExist):
                foo.bazz_cache

        # Get from the (instance) cache
        with self.assertNumQueries(0):
            with self.assertRaises(Bazz.DoesNotExist):
                foo.bazz_cache

        with self.assertNumQueries(1):
            foo = Foo.objects.get(pk=foo.pk)

        # Prove that we haven't put anything into the remote cache
        with self.assertNumQueries(1):
            with self.assertRaises(Bazz.DoesNotExist):
                foo.bazz_cache
