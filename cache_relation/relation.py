from django.db.models.signals import post_save

from .core import get_instance, delete_instance

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
        # Always use the cached "real" instance if available
        try:
            return getattr(self, descriptor.cache_name)
        except AttributeError:
            pass

        # Lookup cached instance
        try:
            return getattr(self, '_%s_cache' % related_name)
        except AttributeError:
            pass

        instance = get_instance(rel.model, self.pk)

        setattr(self, '_%s_cache' % related_name, instance)

        return instance
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
