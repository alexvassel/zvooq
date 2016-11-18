# -*- coding: utf-8 -*-
from tornado.escape import json_decode
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.web import RequestHandler, asynchronous

from helpers import BASE_URL, REQUEST_TIMEOUT, STATUSES, TTL, ERRORS


class Index(RequestHandler):
    key = None
    status_key = None

    @asynchronous
    def get(self):
        self.key = self.get_argument('key')
        self.status_key = self.key + '_status'

        status = self.application.cache.get(self.status_key)

        # Если есть отметка о том, что значение по данному ключу в процессе получения, то выходим.
        if status is not None:
            self.finish(dict(status=status))
            return

        key_value = self.application.cache.get(self.key)

        # Если значение по ключу есть в кэше, то отдаем его и выходим
        if key_value is not None:
            self.finish(dict(status='OK', value=key_value))
            return

        # Если значение пока никто не получает, то отмечаемся, в том, что ушли получать значение
        if status is None:
            self.application.cache.set(self.status_key, STATUSES['pending'], TTL['status'])

        url = BASE_URL.format(self.key)

        request = HTTPRequest(url, request_timeout=REQUEST_TIMEOUT)
        AsyncHTTPClient().fetch(request, callback=self.on_response)

    def on_response(self, response):
        try:
            response = json_decode(response.body)
            # Записываем в кэш значение, полученное от сервера
            self.application.cache.set(self.key, response['hash'], TTL['key'])
            r = dict(status='OK', value=response['hash'])
        except ValueError:
            r = dict(status='ERROR', error=ERRORS['decode'])
        except TypeError:
            r = dict(status='ERROR', error=ERRORS['timeout'])

        '''после ответа от сервера, или таймаута запроса, удаляем информацию о том,
        что мы получали значение'''
        self.application.cache.delete(self.status_key)
        self.finish(r)

