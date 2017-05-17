#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import unittest

import mock
import requests_mock

from webhook_logger.slack import SlackHandler


class TestSlackLogger(unittest.TestCase):
    def setUp(self):
        self.rm = requests_mock.mock()
        self.rm.start()

    def tearDown(self):
        self.rm.stop()

    def _build_logger(self, name, url=None):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        h = SlackHandler(hook_url=url)
        h.setLevel(logging.INFO)
        logger.addHandler(h)
        return logger

    def test_incorrect_config(self):
        logger = self._build_logger('incorrect')
        logger.info("test", extra={'notify_slack': True})
        self.assertEqual(self.rm.call_count, 0)

    def test_correct_config(self):
        self.rm.post('https://some-hook.com/abcde', json={'message': "OK"})
        logger = self._build_logger('basic', 'https://some-hook.com/abcde')
        logger.info("test", extra={'notify_slack': True})
        self.assertEqual(self.rm.call_count, 1)

    @mock.patch('webhook_logger.slack.settings')
    def test_django_config(self, settings):
        settings.SLACK_WEBHOOK_URL = 'https://some-hook.com/abcde'
        self.rm.post('https://some-hook.com/abcde', json={'message': "OK"})
        logger = self._build_logger('django')
        logger.info("Test", extra={'notify_slack': True})
        self.assertEqual(self.rm.call_count, 1)
