# -*- coding: utf-8 -*-

import memcache
from tornado import web

from handlers import main

application = web.Application([
                web.URLSpec(r'/from_cache', main.Index, name='index'),
    ], debug=True)

# Чтобы доступ к кэшу иметь из любого хендлера
application.cache = memcache.Client(['127.0.0.1'])
