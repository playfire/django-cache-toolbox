from cache_toolbox import cache_model, cache_relation

from django.db import models

class Foo(models.Model):
    bar = models.TextField()

class Bazz(models.Model):
    foo = models.OneToOneField(
        Foo,
        related_name='bazz',
        on_delete=models.CASCADE,
        primary_key=True,
    )

    value = models.IntegerField(null=True)

cache_model(Foo)
cache_relation(Foo.bazz)


class ToLoad(models.Model):
    name = models.TextField()

class AlwaysRelated(models.Model):
    to_load = models.OneToOneField(
        ToLoad,
        related_name='always_related',
        on_delete=models.CASCADE,
        primary_key=True,
    )

    value = models.IntegerField(null=True)

cache_model(ToLoad)
cache_relation(ToLoad.always_related, always_fetch=True)
