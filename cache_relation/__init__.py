from django.core.cache import cache
from django.db.models.signals import post_save

def dict_from_instance(obj):
    return dict(
        (x.name, getattr(obj, x.attname)) for x in obj._meta.fields
        if not x.primary_key
    )

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

    def get_cache_key(instance_or_pk):
        return '%s.%s:%s' % (
            rel.model._meta.app_label,
            rel.model._meta.module_name,
            getattr(instance_or_pk, 'pk', instance_or_pk),
        )

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

        cache_key = get_cache_key(self)

        obj = None
        data = cache.get(cache_key)

        if data:
            try:
                # Try and construct instance from dictionary
                obj = rel.model(pk=self.pk, **data)
            except:
                # Error when deserialising - remove from the cache; we will
                # fallback and return the underlying object
                cache.delete(cache_key)

        if obj is None:
            obj = getattr(self, rel.field.related_query_name())

            data = dict(
                (x.name, getattr(obj, x.attname)) for x in obj._meta.fields
                if not x.primary_key
            )
            cache.set(cache_key, data, duration)

        setattr(self, '_%s_cache' % related_name, obj)

        return obj
    setattr(rel.parent_model, related_name, get)

    # Clearing cache

    def clear(self):
        cache.delete(get_cache_key(self))

    @classmethod
    def clear_pk(cls, *instances_or_pk):
        cache.delete_many([get_cache_key(x) for x in instances_or_pk])

    def on_post_save(sender, instance, created, *args, **kwargs):
        cache.delete(get_cache_key(instance))

    setattr(rel.model, '%s_clear' % related_name, clear)
    setattr(rel.parent_model, '%s_clear' % related_name, clear)
    setattr(rel.parent_model, '%s_clear_pk' % related_name, clear_pk)
    post_save.connect(on_post_save, sender=rel.model, weak=False)
