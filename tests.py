# -*- coding: utf-8 -*-

import httplib
import json
import unittest

import mock
from tornado.concurrent import Future
from tornado.escape import json_decode
from tornado.httpclient import HTTPError
from tornado.testing import AsyncHTTPTestCase

from app import application
from handlers.main import Index
from helpers import STATUSES, TTL, ERRORS


class ApplicationTestCase(AsyncHTTPTestCase):
    TEST_PARAM = {'bad_name': 'test', 'good_name': 'key', 'value': '123', 'hash': 'hash'}

    def get_app(self):
        return application

    def test_index(self):
        """проверяем, что без параметра сервис отдает 400"""
        response = self.fetch(self.get_app().reverse_url('index'))
        self.assertEqual(response.code, httplib.BAD_REQUEST)
        response = (self.fetch(self.get_app().reverse_url('index') + '?{}={}'.
                               format(self.TEST_PARAM['bad_name'], self.TEST_PARAM['value'])))
        self.assertEqual(response.code, httplib.BAD_REQUEST)

    @mock.patch('handlers.main.Index.fetch')
    @mock.patch('app.application.cache')
    def test_status_cache_exists(self, cache, fetch):
        """проверяем, что если стоит кэш, на получения значения, мы не делаем запрос на удаленный сервис"""
        cache.get.return_value = STATUSES['pending']
        response = (self.fetch(self.get_app().reverse_url('index') + '?{}={}'.
                               format(self.TEST_PARAM['good_name'], self.TEST_PARAM['value'])))
        self.assertDictEqual(json_decode(response.body), {'status': STATUSES['pending']})
        cache.get.assert_called_once_with(self.TEST_PARAM['value'] + '_status')
        fetch.assert_not_called()
        self.assertDictEqual(json.loads(response.body), dict(status=STATUSES['pending']))

    @mock.patch('handlers.main.Index.fetch')
    @mock.patch('app.application.cache')
    def test_key_cache_exists(self, cache, fetch):
        """проверяем, что если в кэше уже дежит хэш, мы не делаем запрос на удаленный сервис"""
        cache.get.side_effect = (None, self.TEST_PARAM['hash'])
        response = (self.fetch(self.get_app().reverse_url('index') + '?{}={}'.
                               format(self.TEST_PARAM['good_name'], self.TEST_PARAM['value'])))
        self.assertDictEqual(json_decode(response.body), {'status': 'OK',
                                                          'value': self.TEST_PARAM['hash']})
        self.assertEquals(cache.get.call_count, 2)
        self.assertListEqual(cache.get.mock_calls, ([mock.call(self.TEST_PARAM['value'] +
                                                     '_status'),
                                                     mock.call(self.TEST_PARAM['value'])]))
        fetch.assert_not_called()
        self.assertDictEqual(json.loads(response.body), dict(status=STATUSES['ok'],
                                                             value=self.TEST_PARAM['hash']))

    @mock.patch('handlers.main.Index.fetch')
    @mock.patch('app.application.cache')
    def test_http_call(self, cache, fetch):
        """проверяем, что если кэш пуст, мы делаем запрос на удаленный сервис"""
        cache.get.side_effect = (None, None)

        future = Future()
        future.set_result(json.dumps({'hash': self.TEST_PARAM['hash']}))
        fetch.return_value = future

        response = (self.fetch(self.get_app().reverse_url('index') + '?{}={}'.
                               format(self.TEST_PARAM['good_name'], self.TEST_PARAM['value'])))
        self.assertEqual(response.code, httplib.OK)
        self.assertEquals(cache.get.call_count, 2)
        self.assertListEqual(cache.get.mock_calls, ([mock.call(self.TEST_PARAM['value'] +
                                                     '_status'),
                                                     mock.call(self.TEST_PARAM['value'])]))
        self.assertEquals(cache.set.call_count, 2)
        self.assertListEqual(cache.set.mock_calls, ([mock.call(self.TEST_PARAM['value'] +
                                                     '_status', STATUSES['pending'],
                                                               TTL['status']),
                                                     mock.call(self.TEST_PARAM['value'],
                                                               self.TEST_PARAM['hash'],
                                                               TTL['key'])]))
        self.assertDictEqual(json.loads(response.body), dict(status=STATUSES['ok'],
                                                             value=self.TEST_PARAM['hash']))

    def test_handle_response(self):
        """проверяем, что ошибки обрабатываются должным образом"""
        r = Index.handle_errors(HTTPError(httplib.INTERNAL_SERVER_ERROR))
        self.assertDictEqual(r, dict(status=STATUSES['error'], error=ERRORS['decode']))
        r = Index.handle_errors(HTTPError(httplib.SEE_OTHER))
        self.assertDictEqual(r, dict(status=STATUSES['error'], error=ERRORS['timeout']))


if __name__ == '__main__':
    unittest.main()
