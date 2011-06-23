from django.db.models.signals import post_save, post_delete

from .core import get_instance, delete_instance

def cache_model(model, timeout=None):
    if hasattr(model, 'get_cached'):
        # Already patched
        return

    def clear_cache(sender, instance, *args, **kwargs):
        delete_instance(sender, instance)

    post_save.connect(clear_cache, sender=model, weak=False)
    post_delete.connect(clear_cache, sender=model, weak=False)

    @classmethod
    def get(cls, pk):
        if pk is None:
            return None
        return get_instance(cls, pk, timeout)

    model.get_cached = get
