from django.db.models.signals import post_save, post_delete

from .core import get_instance, delete_instance

def cache_model(model, duration=60 * 60 * 24 * 3):
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
        return get_instance(cls, pk, duration)

    model.get_cached = get
