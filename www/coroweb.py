#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError

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


