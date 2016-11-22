# -*- coding: utf-8 -*-

from tornado import ioloop, httpserver

from app import application


http_server = httpserver.HTTPServer(application)
http_server.listen(5000, address='0.0.0.0')
ioloop.IOLoop.current().start()
