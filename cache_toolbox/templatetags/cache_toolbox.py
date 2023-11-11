from django import template
from django.core.cache import cache
from django.template import Node, TemplateSyntaxError, Variable

register = template.Library()


class CacheNode(Node):
    def __init__(self, nodelist, expire_time, key):
        self.nodelist = nodelist
        self.expire_time = Variable(expire_time)
        self.key = Variable(key)

    def render(self, context):
        key = self.key.resolve(context)
        expire_time = int(self.expire_time.resolve(context))

        value = cache.get(key)
        if value is None:
            value = self.nodelist.render(context)
            cache.set(key, value, expire_time)
        return value


@register.tag
def cachedeterministic(parser, token):
    """
    This will cache the contents of a template fragment for a given amount of
    time, just like {% cache .. %} except that the key is deterministic and not
    mangled or run through MD5.

    Usage::

        {% cachedeterministic [expire_time] [key] %}
            .. some expensive processing ..
        {% endcachedeterministic %}

    """
    nodelist = parser.parse(("endcachedeterministic",))
    parser.delete_first_token()
    tokens = token.contents.split()
    if len(tokens) != 3:
        raise TemplateSyntaxError(u"'%r' tag requires 2 arguments." % tokens[0])
    return CacheNode(nodelist, tokens[1], tokens[2])


class ShowIfCachedNode(Node):
    def __init__(self, key):
        self.key = Variable(key)

    def render(self, context):
        key = self.key.resolve(context)
        return cache.get(key) or ""


@register.tag
def showifcached(parser, token):
    """
    Show content if it exists in the cache, otherwise display nothing.

    The key is entirely deterministic and not mangled or run through MD5 (cf.
    {% cache %})

    Usage::

        {% showifcached [key] %}

    """
    tokens = token.contents.split()
    if len(tokens) != 2:
        raise TemplateSyntaxError(u"'%r' tag requires 1 argument." % tokens[0])
    return ShowIfCachedNode(tokens[1])
