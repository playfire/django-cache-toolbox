from django.core.cache import cache

def cache_key(model, instance_or_pk):
    return '%s.%s:%d' % (
        model._meta.app_label,
        model._meta.module_name,
        getattr(instance_or_pk, 'pk', instance_or_pk),
    )

def get_instance(model, instance_or_pk, duration=None):
    pk = getattr(instance_or_pk, 'pk', instance_or_pk)
    key = cache_key(model, instance_or_pk)
    data = cache.get(key)

    if data is not None:
        try:
            # Try and construct instance from dictionary
            instance = model(pk=pk, **data)

            # Ensure instance knows that it already exists in the database,
            # otherwise we will fail any uniqueness checks when saving the
            # instance.
            instance._state.adding = False

            return instance
        except:
            # Error when deserialising - remove from the cache; we will
            # fallback and return the underlying instance
            cache.delete(key)

    # Use the default manager so we are never filtered by a .get_query_set()
    instance = model._default_manager.get(pk=pk)

    data = {}
    for field in instance._meta.fields:
        # Harmless to save, but saves space in the dictionary - we already know
        # the primary key when we lookup
        if field.primary_key:
            continue

        if field.get_internal_type() == 'FileField':
            # Prevent problems with DNImageField by not serialising it.
            continue

        data[field.attname] = getattr(instance, field.attname)

    cache.set(key, data, duration)

    return instance

def delete_instance(model, *instance_or_pk):
    cache.delete_many([cache_key(model, x) for x in instance_or_pk])
