# -*- coding: utf-8 -*-

BASE_URL = 'https://vast-eyrie-4711.herokuapp.com/?key={}'

# В секундах
REQUEST_TIMEOUT = 5

# Врем жизни ключей в секундах (кэш для статуса обработки запроса и кэш для ключа)
'''Время жизни кэша статуса нужно для ситуаций, когда поток с получением ключа проставил статус,
но по каким-то причинам "отвалился"'''
TTL = dict(key=9, status=6)

# Означает, что поток начал обращение к BASE_URL за ответом
STATUSES = dict(pending='PENDING', error='ERROR', ok='OK')

# Ошибки таймаута и получение хэша по ключу
ERRORS = dict(timeout='timeout error', decode='json decode error')
