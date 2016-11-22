# -*- coding: utf-8 -*-

import httplib

from tornado.escape import json_decode
import tornado.gen
from tornado.httpclient import HTTPRequest, AsyncHTTPClient, HTTPError
from tornado.web import RequestHandler

from helpers import BASE_URL, REQUEST_TIMEOUT, STATUSES, TTL, ERRORS


class Index(RequestHandler):
    key = None
    status_key = None

    @tornado.gen.coroutine
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
        self.application.cache.set(self.status_key, STATUSES['pending'], TTL['status'])

        url = BASE_URL.format(self.key)

        try:
            response = yield self.fetch(url)
        except HTTPError as e:
            self.finish(self.handle_errors(e))
            return
        finally:
            self.application.cache.delete(self.status_key)

        response = json_decode(response)

        self.application.cache.set(self.key, response['hash'], TTL['key'])
        self.finish(dict(status='OK', value=response['hash']))

    @tornado.gen.coroutine
    def fetch(self, url):
        request = HTTPRequest(url, request_timeout=REQUEST_TIMEOUT)
        response = yield AsyncHTTPClient().fetch(request)
        raise tornado.gen.Return(response.body)

    @staticmethod
    def handle_errors(e):
        msg = ERRORS['decode'] if e.code == httplib.INTERNAL_SERVER_ERROR else ERRORS['timeout']
        return dict(status=STATUSES['error'], error=msg)
