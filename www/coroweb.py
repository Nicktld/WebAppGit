#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from errors import APIError

# Build Handler Decorator to store URL information
def Handler_decorator(path, *, method):
    def decorator(func):
        @functools.wraps(func)
        def warpper(*args, **kw):
            return func(*args, **kw)
        warpper.__route__ = path
        warpper.__method__ = method
        return warpper
    return decorator
# Partial Function for GET, POST
get = functools.partial(Handler_decorator, method = 'GET')
post = functools.partial(Handler_decorator, method = 'POST')
put = functools.partial(Handler_decorator, method='PUT')
delete = functools.partial(Handler_decorator, method='DELETE')



# RequestHandler aims to parse URL-function-required arguments, then get those from request
# URL handlers may not be coroutines. Hence, RequestHandler should transform it.
# Call URL hanlders then return a web.Response which can be passed to aiohttp
class RequestHandler(object):  

    def __init__(self, func):# Initialization with a URL handler
        self._func = asyncio.coroutine(func)

    async def __call__(self, request):  # Make an instance callable{ RequestHandler(handler1)(request) } which is required by aiohttp

        required_args = inspect.signature(self._func).parameters# Get handler arguments
        logging.info('required args: %s' % required_args)

        # Get arguments from GET or POST, add the one if it is a handler-required argument
        kw = {arg: value for arg, value in request.__data__.items() if arg in required_args}

        # Use match_info for arguments，such as 'id' from @get('/blog/{id}')
        kw.update(request.match_info)

        # Also include request in case of handler1(request)
        if 'request' in required_args:
            kw['request'] = request

        # Check the integrity of handler arguments
        for key, arg in required_args.items():
            
            # request argument cannot be in VAR kinds
            if key == 'request' and arg.kind in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                return web.HTTPBadRequest(text='request parameter cannot be the var argument.')
            
            # An argument can be omitted if it does not belong to VAR kinds
            if arg.kind not in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                # If there is no default value for the argument, raise an error.
                if arg.default == arg.empty and arg.name not in kw:
                    return web.HTTPBadRequest(text='Missing argument: %s' % arg.name)

        logging.info('call with args: %s' % kw)
        try:
            return await self._func(**kw)
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


# Add all routes of a module
def add_routes(app, module_name):
    try:
        mod = __import__(module_name, fromlist=['get_submodule'])
        #If fromlist is None, __import__ will not include the submodules
    except ImportError as e:
        raise e
    
    # Traverse atrributes of a module
    # Our URL hanlders are decorated by @get or @post, therefore there would be '__method__' and '__route__' attributes there.
    for attr in dir(mod):
        # Exclude the attributes starting with '_'
        if attr.startswith('_'):
            continue
        func = getattr(mod, attr)

        # Get handlers that have attributes of __method___ and __route__
        if callable(func) and hasattr(func, '__method__') and hasattr(func, '__route__'):
            args = ', '.join(inspect.signature(func).parameters.keys())
            logging.info('add route %s %s => %s(%s)' % (func.__method__, func.__route__, func.__name__, args))
            app.router.add_route(func.__method__, func.__route__, RequestHandler(func))

# Add routes of static files
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))
