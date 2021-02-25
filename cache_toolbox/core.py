"""
Core methods
------------

.. autofunction:: cache_toolbox.core.get_instance
.. autofunction:: cache_toolbox.core.delete_instance
.. autofunction:: cache_toolbox.core.instance_key

"""

try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.core.cache import cache
from django.db import DEFAULT_DB_ALIAS, transaction

from . import app_settings


CACHE_FORMAT_VERSION = 2


def setattrdefault(obj, name, default):
    try:
        return getattr(obj, name)
    except AttributeError:
        setattr(obj, name, default)
        return default


def get_related_name(descriptor):
    return "%s_cache" % descriptor.related.field.related_query_name()


def get_related_cache_name(related_name: str) -> str:
    return "_%s_cache" % related_name


def add_always_fetch_relation(descriptor):
    setattrdefault(
        descriptor.related.model,
        "_cache_fetch_related",
        [],
    ).append(descriptor)


def serialise(instance):
    data = {}
    for field in instance._meta.fields:
        # Harmless to save, but saves space in the dictionary - we already know
        # the primary key when we lookup
        if field.primary_key:
            continue

        # We also don't want to save any virtual fields.
        if not field.concrete:
            continue

        data[field.attname] = getattr(instance, field.attname)

    # Encode through Pickle, since that allows overriding and covers (most)
    # Python types we'd want to serialise.
    return pickle.dumps(data, protocol=-1)


def deserialise(model, data, pk, using):
    # Try and construct instance from dictionary
    instance = model(pk=pk, **pickle.loads(data))

    # Ensure instance knows that it already exists in the database,
    # otherwise we will fail any uniqueness checks when saving the
    # instance.
    instance._state.adding = False

    # Specify database so that instance is setup correctly. We don't
    # namespace cached objects by their origin database, however.
    instance._state.db = using or DEFAULT_DB_ALIAS

    return instance


def get_instance(model, instance_or_pk, timeout=None, using=None):
    """
    Returns the ``model`` instance with a primary key of ``instance_or_pk``.

    If the data is cached it will be returned from there, otherwise the regular
    Django ORM is queried for this instance and the data stored in the cache.

    If omitted, the timeout value defaults to
    ``settings.CACHE_TOOLBOX_DEFAULT_TIMEOUT`` instead of 0 (zero).

    Example::

        >>> get_instance(User, 1) # Cache miss
        <User: lamby>
        >>> get_instance(User, 1) # Cache hit
        <User: lamby>
        >>> User.objects.get(pk=1) == get_instance(User, 1)
        True
    """

    pk = getattr(instance_or_pk, "pk", instance_or_pk)

    primary_model = model
    descriptors = getattr(primary_model, "_cache_fetch_related", ())
    models = [model, *(d.related.field.model for d in descriptors)]
    # Note: we're assuming that the relations are primary key foreign keys, and
    # so all have the same primary key. This matches the assumption which
    # `cache_relation` makes.
    keys_to_models = {instance_key(model, instance_or_pk): model for model in models}

    data_map = cache.get_many(tuple(keys_to_models.keys()))
    instance_map = {}

    if data_map.keys() == keys_to_models.keys():
        try:
            for key, data in data_map.items():
                model = keys_to_models[key]
                instance_map[key] = deserialise(model, data, pk, using)
        except:
            # Error when deserialising - remove from the cache; we will
            # fallback and return the underlying instance
            cache.delete_many(tuple(keys_to_models.keys()))

        else:
            key = instance_key(primary_model, instance_or_pk)
            primary_instance = instance_map[key]

            for descriptor in descriptors:
                related_instance = instance_map[
                    instance_key(
                        descriptor.related.field.model,
                        instance_or_pk,
                    )
                ]
                related_cache_name = get_related_cache_name(
                    get_related_name(descriptor),
                )
                setattr(primary_instance, related_cache_name, related_instance)

            return primary_instance

    related_names = [d.related.field.related_query_name() for d in descriptors]

    # Use the default manager so we are never filtered by a .get_query_set()
    queryset = primary_model._default_manager.using(using)
    if related_names:
        # NB: select_related without args selects all it can find, which we don't want.
        queryset = queryset.select_related(*related_names)
    primary_instance = queryset.get(pk=pk)

    instances = [
        primary_instance,
        *(getattr(primary_instance, x, None) for x in related_names),
    ]

    cache_data = {}
    for instance in instances:
        if instance is None:
            continue

        key = instance_key(instance._meta.model, instance)
        cache_data[key] = serialise(instance)

    if timeout is None:
        timeout = app_settings.CACHE_TOOLBOX_DEFAULT_TIMEOUT

    cache.set_many(cache_data, timeout)

    return primary_instance


def delete_instance(model, *instance_or_pk):
    """
    Purges the cache keys for the instances of this model.
    """

    # Only clear the cache when the current transaction commits.
    # While clearing the cache earlier than that is valid, it is insufficient
    # to ensure cache consistency. There is a possible race between two
    # transactions as follows:
    #
    #   Transaction 1: modifies model (and thus clears cache)
    #   Transaction 2: queries cache, which misses, so it populates the cache
    #                  from the database, picking up the unmodified model
    #   Transaction 1: commits, without further signal to the cache
    #
    # At this point the cache contains the _original_ value of the model, which
    # is out of step with the database.
    # To avoid this we delay clearing the cache until the transaction commits.
    # While this does leave a small window after the transaction has committed
    # but before the cache has cleared, that is better than leaving the cache
    # incorrect until the model is next updated.

    transaction.on_commit(
        lambda: cache.delete_many(
            [instance_key(model, x) for x in instance_or_pk],
        )
    )


def instance_key(model, instance_or_pk):
    """
    Returns the cache key for this (model, instance) pair.
    """

    return "cache.%d:%s.%s:%s" % (
        CACHE_FORMAT_VERSION,
        model._meta.app_label,
        model._meta.model_name,
        getattr(instance_or_pk, "pk", instance_or_pk),
    )
