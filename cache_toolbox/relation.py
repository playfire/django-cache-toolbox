"""
Caching instances via ``related_name``
--------------------------------------

``cache_relation`` adds utility methods to a model to obtain ``related_name``
instances via the cache.

Usage
~~~~~

::

    from django.db import models
    from django.contrib.auth.models import User

    class Foo(models.Model):
        user = models.OneToOneField(
            User,
            primary_key=True,
            related_name='foo',
        )

        name = models.CharField(max_length=20)

    cache_relation(User.foo)

(``primary_key`` being ``True`` is currently required.)
::

    >>> user = User.objects.get(pk=1)
    >>> user.foo_cache # Cache miss - hits the database
    <Foo: >
    >>> user = User.objects.get(pk=1)
    >>> user.foo_cache # Cache hit - no database access
    <Foo: >
    >>> user = User.objects.get(pk=2)
    >>> user.foo # Regular lookup - hits the database
    <Foo: >
    >>> user.foo_cache # Special-case: Will not hit cache or database.
    <Foo: >

Accessing ``user_instance.foo_cache`` (note the "_cache" suffix) will now
obtain the related ``Foo`` instance via the cache. Accessing the original
``user_instance.foo`` attribute will perform the lookup as normal.

Invalidation
~~~~~~~~~~~~

Upon saving (or deleting) the instance, the cache is cleared. For example::

    >>> user = User.objects.get(pk=1)
    >>> foo = user.foo_cache # (Assume cache hit from previous session)
    >>> foo.name = "New name"
    >>> foo.save() # Cache is cleared on save
    >>> user = User.objects.get(pk=1)
    >>> user.foo_cache # Cache miss.
    <Foo: >

Manual invalidation may also be performed using the following methods::

    >>> user_instance.foo_cache_clear()
    >>> User.foo_cache_clear_fk(user_instance_pk)

Manual invalidation is required if you use ``.update()`` methods which the
``post_save`` and ``post_delete`` hooks cannot intercept.

Support
~~~~~~~

``cache_relation`` currently only works with ``OneToOneField`` fields. Support
for regular ``ForeignKey`` fields is planned.
"""

from django.db.models.signals import post_save, post_delete

from .core import (
    get_instance,
    delete_instance,
    get_related_name,
    get_related_cache_name,
    add_always_fetch_relation,
)


def cache_relation(descriptor, timeout=None, *, always_fetch=False):
    rel = descriptor.related

    if not rel.field.primary_key:
        # This is an internal limitation due to the way that we construct our
        # cache keys.
        raise ValueError("Cached relations must be the primary key")

    if always_fetch:
        add_always_fetch_relation(descriptor)

    related_name = get_related_name(descriptor)

    @property
    def get(self):
        # Always use the cached "real" instance if available
        if descriptor.is_cached(self):
            return descriptor.__get__(self)

        # Lookup cached instance
        related_cache_name = get_related_cache_name(related_name)
        try:
            instance = getattr(self, related_cache_name)
        except AttributeError:
            # no local cache
            pass
        else:
            if instance is None:
                # we (locally) cached that there is no model
                raise descriptor.RelatedObjectDoesNotExist(
                    "%s has no %s."
                    % (
                        rel.model.__name__,
                        related_name,
                    ),
                )
            return instance

        try:
            instance = get_instance(
                rel.field.model,
                # Note that we're using _our_ primary key here, rather than the
                # primary key of the model being cached. This is ok since we
                # know that its primary key is a foreign key to this model
                # instance and therefore has the same value.
                self.pk,
                timeout,
                using=self._state.db,
            )
            setattr(self, related_cache_name, instance)
        except rel.related_model.DoesNotExist:
            setattr(self, related_cache_name, None)
            raise descriptor.RelatedObjectDoesNotExist(
                "%s has no %s."
                % (
                    rel.model.__name__,
                    related_name,
                ),
            )

        return instance

    setattr(rel.model, related_name, get)

    # Clearing cache

    def clear(self):
        delete_instance(rel.related_model, self)

    @classmethod
    def clear_pk(cls, *instances_or_pk):
        delete_instance(rel.related_model, *instances_or_pk)

    def clear_cache(sender, instance, *args, **kwargs):
        delete_instance(rel.related_model, instance)

    setattr(rel.model, "%s_clear" % related_name, clear)
    setattr(rel.model, "%s_clear_pk" % related_name, clear_pk)

    post_save.connect(clear_cache, sender=rel.related_model, weak=False)
    post_delete.connect(clear_cache, sender=rel.related_model, weak=False)
