from cache_toolbox.core import delete_instance

from django.core.cache import cache
from django.test import TransactionTestCase

from .models import AlwaysRelated, ToLoad


# Use `TransactionTestCase` so that our `on_commit` actions happen when we expect.
class CachedGetRelatedTest(TransactionTestCase):
    def setUp(self):
        self.to_load = ToLoad.objects.create(name="bees")
        self.always_related = AlwaysRelated.objects.create(to_load=self.to_load)
        self._populate_cache()

    def _populate_cache(self):
        ToLoad.get_cached(self.to_load.pk)

    def test_cached_get(self):
        # Get from the cache
        cached_object = ToLoad.get_cached(self.to_load.pk)

        # Validate that we're using the value we pre-loaded
        cache.clear()

        with self.assertNumQueries(0):
            self.assertEqual(self.to_load.name, cached_object.name)
            self.assertEqual(
                self.always_related,
                cached_object.always_related_cache,
            )

    def test_cached_get_primary_absent_from_cache(self):
        # Remove the instance from the cache, for example as a result of it
        # being saved.
        delete_instance(ToLoad, self.to_load)

        with self.assertNumQueries(1):
            # Get from the cache - this will involve actually loading from the
            # database.
            cached_object = ToLoad.get_cached(self.to_load.pk)

        # Validate that we're using the value we pre-loaded
        cache.clear()

        with self.assertNumQueries(0):
            self.assertEqual(self.to_load.name, cached_object.name)
            self.assertEqual(
                self.always_related,
                cached_object.always_related_cache,
            )

    def test_cached_get_relation_absent_from_cache(self):
        # Remove the instance from the cache, for example as a result of it
        # being saved.
        delete_instance(AlwaysRelated, self.always_related)

        # Attempt to load, should fall back to the database due to the lack of
        # the related instance in the cache results.
        with self.assertNumQueries(1):
            cached_object = ToLoad.get_cached(self.to_load.pk)

        self.assertEqual(self.to_load.name, cached_object.name)

        with self.assertNumQueries(0):
            self.assertEqual(self.to_load.name, cached_object.name)
            self.assertEqual(
                self.always_related,
                cached_object.always_related_cache,
            )

    def test_cached_get_no_relation(self):
        self.always_related.delete()

        # Get from the cache
        cached_object = ToLoad.get_cached(self.to_load.pk)

        self.assertEqual(self.to_load.name, cached_object.name)

        with self.assertNumQueries(0):
            with self.assertRaises(AlwaysRelated.DoesNotExist):
                cached_object.always_related_cache

        # Sanity check
        with self.assertRaises(AlwaysRelated.DoesNotExist):
            cached_object.always_related

    def test_cached_get_no_relation_no_cache(self):
        self.always_related.delete()
        cache.clear()

        # Attempt to load, should fall back to the database and should handle
        # the lack of the related instance.
        with self.assertNumQueries(1):
            cached_object = ToLoad.get_cached(self.to_load.pk)

        self.assertEqual(self.to_load.name, cached_object.name)

        with self.assertNumQueries(0):
            with self.assertRaises(AlwaysRelated.DoesNotExist):
                cached_object.always_related_cache

        # Sanity check
        with self.assertNumQueries(0):
            with self.assertRaises(AlwaysRelated.DoesNotExist):
                cached_object.always_related
