# -*- coding: utf-8 -*-

import httplib
import json
import unittest

import mock
from tornado.concurrent import Future
from tornado.escape import json_decode
from tornado.testing import AsyncHTTPTestCase

from app import application
from helpers import STATUSES, TTL


class ApplicationTestCase(AsyncHTTPTestCase):
    TEST_PARAM = {'bad_name': 'test', 'good_name': 'key', 'value': '123', 'hash': 'hash'}

    def get_app(self):
        return application

    def test_index(self):
        response = self.fetch(self.get_app().reverse_url('index'))
        self.assertEqual(response.code, httplib.BAD_REQUEST)
        response = (self.fetch(self.get_app().reverse_url('index') + '?{}={}'.
                               format(self.TEST_PARAM['bad_name'], self.TEST_PARAM['value'])))
        self.assertEqual(response.code, httplib.BAD_REQUEST)

    @mock.patch('handlers.main.Index.fetch')
    @mock.patch('app.application.cache')
    def test_status_cache_exists(self, cache, fetch):
        cache.get.return_value = STATUSES['pending']
        response = (self.fetch(self.get_app().reverse_url('index') + '?{}={}'.
                               format(self.TEST_PARAM['good_name'], self.TEST_PARAM['value'])))
        self.assertDictEqual(json_decode(response.body), {'status': STATUSES['pending']})
        cache.get.assert_called_once_with(self.TEST_PARAM['value'] + '_status')
        fetch.assert_not_called()

    @mock.patch('handlers.main.Index.fetch')
    @mock.patch('app.application.cache')
    def test_key_cache_exists(self, cache, fetch):
        cache.get.side_effect = (None, self.TEST_PARAM['value'])
        response = (self.fetch(self.get_app().reverse_url('index') + '?{}={}'.
                               format(self.TEST_PARAM['good_name'], self.TEST_PARAM['value'])))
        self.assertDictEqual(json_decode(response.body), {'status': 'OK',
                                                          'value': self.TEST_PARAM['value']})
        self.assertEquals(cache.get.call_count, 2)
        self.assertListEqual(cache.get.mock_calls, ([mock.call(self.TEST_PARAM['value'] +
                                                     '_status'),
                                                     mock.call(self.TEST_PARAM['value'])]))
        fetch.assert_not_called()

    @mock.patch('handlers.main.Index.fetch')
    @mock.patch('app.application.cache')
    def test_http_call(self, cache, fetch):
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


if __name__ == '__main__':
    unittest.main()
