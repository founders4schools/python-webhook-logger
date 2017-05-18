#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import unittest
from logging.config import dictConfig

import mock
import requests_mock

from webhook_logger.slack import SlackHandler, SlackLogFilter

DICT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'notify_slack': {
            '()': 'webhook_logger.slack.SlackLogFilter',
        }
    },
    'handlers': {
        'slack': {
            'level': 'INFO',
            'filters': ['notify_slack'],
            'class': 'webhook_logger.slack.SlackHandler',
            'hook_url': 'https://my-super-hooks.com/12345',
        }
    },
    'loggers': {
        'dict_config': {
            'handlers': ['slack'],
            'level': 'DEBUG'
        }
    }
}


class TestSlackLogger(unittest.TestCase):
    def setUp(self):
        self.rm = requests_mock.mock()
        self.rm.start()

    def tearDown(self):
        self.rm.stop()

    def _build_logger(self, name, url=None, filter=False):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        h = SlackHandler(hook_url=url)
        if filter:
            h.addFilter(SlackLogFilter())
        h.setLevel(logging.INFO)
        logger.addHandler(h)
        return logger

    def test_incorrect_config(self):
        logger = self._build_logger('incorrect')
        logger.info("test")
        self.assertEqual(self.rm.call_count, 0)

    def test_correct_config(self):
        self.rm.post('https://some-hook.com/abcde', json={'message': "OK"})
        logger = self._build_logger('basic', 'https://some-hook.com/abcde')
        logger.info("test")
        self.assertEqual(self.rm.call_count, 1)

    @mock.patch('webhook_logger.slack.settings')
    def test_django_config(self, settings):
        settings.SLACK_WEBHOOK_URL = 'https://some-hook.com/abcde'
        self.rm.post('https://some-hook.com/abcde', json={'message': "OK"})
        logger = self._build_logger('django')
        logger.info("Test")
        self.assertEqual(self.rm.call_count, 1)

    def test_filtering_out(self):
        self.rm.post('https://some-hook.com/abcde', json={'message': "OK"})
        logger = self._build_logger('filter_out', 'https://some-hook.com/abcde', True)
        logger.info("test")
        self.assertEqual(self.rm.call_count, 0)

    def test_filtering_in(self):
        self.rm.post('https://some-hook.com/abcde', json={'message': "OK"})
        logger = self._build_logger('filter_in', 'https://some-hook.com/abcde', True)
        logger.info("test", extra={'notify_slack': True})
        self.assertEqual(self.rm.call_count, 1)

    def test_dict_config(self):
        dictConfig(DICT_CONFIG)
        logger = logging.getLogger('dict_config')
        self.rm.post('https://my-super-hooks.com/12345', json={'message': "OK"})
        logger.info("Test", extra={'notify_slack': True})
        self.assertEqual(self.rm.call_count, 1)
