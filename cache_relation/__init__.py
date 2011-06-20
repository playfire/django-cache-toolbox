from django.core.cache import cache
from django.db.models.signals import post_save

def cache_relation(descriptor, duration=60 * 60 * 24 * 3):
    """
    Usage::

        from django.db import models
        from django.contrib.auth.models import User

        class Foo(models.Model):
            user = models.ForeignKey(User)

        cache_relation(User.foo)

    Then replace ``user_instance.foo`` with ``user_instance.foo_cache``.
    """

    rel = descriptor.related
    related_name = '%s_cache' % rel.field.related_query_name()

    @property
    def get(self):
        # Always use the cached "real" object if available
        try:
            return getattr(self, descriptor.cache_name)
        except AttributeError:
            pass

        # Lookup cached object
        try:
            return getattr(self, '_%s_cache' % related_name)
        except AttributeError:
            pass

        obj = get_instance(rel.model, self.pk)

        setattr(self, '_%s_cache' % related_name, obj)

        return obj
    setattr(rel.parent_model, related_name, get)

    # Clearing cache

    def clear(self):
        delete_instance(rel.model, self)

    @classmethod
    def clear_pk(cls, *instances_or_pk):
        delete_instance(rel.model, *instances_or_pk)

    def on_post_save(sender, instance, created, *args, **kwargs):
        delete_instance(rel.model, instance)

    setattr(rel.model, '%s_clear' % related_name, clear)
    setattr(rel.parent_model, '%s_clear' % related_name, clear)
    setattr(rel.parent_model, '%s_clear_pk' % related_name, clear_pk)
    post_save.connect(on_post_save, sender=rel.model, weak=False)

def _cache_key(model, instance_or_pk):
    return '%s.%s:%d' % (
        model._meta.app_label,
        model._meta.module_name,
        getattr(instance_or_pk, 'pk', instance_or_pk),
    )

def get_instance(model, instance_or_pk, duration=None):
    pk = getattr(instance_or_pk, 'pk', instance_or_pk)
    key = _cache_key(model, instance_or_pk)
    data = cache.get(key)

    if data is not None:
        try:
            # Try and construct instance from dictionary
            obj = model(pk=pk, **data)

            # Ensure instance knows that it already exists in the database,
            # otherwise we will fail any uniqueness checks when saving the
            # instance.
            obj._state.adding = False

            return obj
        except:
            # Error when deserialising - remove from the cache; we will
            # fallback and return the underlying object
            cache.delete(key)

    # Use the default manager so we are never filtered by a .get_query_set()
    obj = model._default_manager.get(pk=pk)

    data = dict(
        (x.attname, getattr(obj, x.attname)) for x in obj._meta.fields
        if not x.primary_key
    )
    cache.set(key, data, duration)

    return obj

def delete_instance(model, *instance_or_pk):
    cache.delete_many([_cache_key(model, x) for x in instance_or_pk])
