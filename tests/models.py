from cache_toolbox import cache_model

from django.db import models

class Foo(models.Model):
    bar = models.TextField()

cache_model(Foo)
