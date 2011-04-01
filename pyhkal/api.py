# encoding: utf-8

import re
import json
import twisted.internet.defer
from functools import partial, wraps
from inspect import getargspec, currentframe
from pyhkal.engine import Pyhkal
from pyhkal import shrink

#XXX functions should eventually go into their respective modules and expose
#    can become a plain list

api = {}
statics = {}
def apply(service):
    applied = dict((name, partial(func, service)) for name, func in api.iteritems())
    applied.update(statics)
    #XXX hack until davenport grows into a full API
    applied['davenport'] = service.davenport
    return applied

def expose(item_or_name, item=None, static=False):
    """
    >>> expose(obj) # requires obj to have __name__ attribute
    >>> @expose
    ... def func(): pass
    ...
    >>> expose("name", obj)
    """
    global statics, api
    dest = statics if static else api
    if item is not None:
        dest[item_or_name] = item
    else:
        dest[item_or_name.__name__] = item_or_name

expose('Identity', shrink.IdentityProxy)
expose(shrink.Avatar, static=True)
expose(shrink.Event, static=True)
expose(shrink.Location, static=True)
expose(shrink.MultitonMeta, static=True)
expose(Pyhkal.dispatch_command)
expose(Pyhkal.dispatch_event)
expose(Pyhkal.twist)
expose('defer', twisted.internet.defer, static=True)

@expose
def hook(service, event, expr=None):
    if expr:
        comp_re = re.compile(expr, re.UNICODE)

    def deco(func):
        if expr:
            @wraps(func)
            def new_func(event):
                matches = comp_re.finditer(event.content)
                for match in matches:
                    if match.groupdict():
                        func(event, **match.groupdict())
                    else:
                        func(event, *match.groups())
        else:
            new_func = func

        service.add_listener(event, new_func)
        return new_func
    return deco


@expose
def register(service, func_or_name):
    if isinstance(func_or_name, basestring):
        def wrapper(func):
            service.add_command(func_or_name, func)
            return func
        return wrapper
    service.add_command(func_or_name.__name__, func_or_name)
    return func_or_name


@expose
def chaos(service, name, script):
    mod = currentframe().f_back.f_globals['__mod__']
    service.davenport.order(mod, name, script)
    def call(cb=None, **kwargs):
        if 'key' in kwargs:
            kwargs['key'] = json.dumps(kwargs['key'])
        d = service.davenport.openView(mod, name, **kwargs)
        if cb is not None:
            d.addCallback(cb)
        return d
    return call

_none = object()
@expose
def remember(service, breadcrumbs, default=_none):
    """Remember that random fact that popped into your head 2 AM in the
    morning. For some weird reason, you need a sofa to remember.

    """
    config = service.screwdriver
    try:
        return reduce(lambda doc, value: doc[value],
                breadcrumbs.split(), config)
    except KeyError:
        if default is not _none:
            return default
        raise
