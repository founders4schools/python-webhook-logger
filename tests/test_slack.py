#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import unittest
from logging.config import dictConfig

import mock
import requests
import requests_mock

from webhook_logger.slack import SlackHandler, SlackLogFilter, SlackFormatter

DICT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'notify_slack': {
            '()': 'webhook_logger.slack.SlackLogFilter',
        }
    },
    'formatters': {
        'slack_format': {
            '()': 'webhook_logger.slack.SlackFormatter',
        },
    },
    'handlers': {
        'slack': {
            'level': 'INFO',
            'filters': ['notify_slack'],
            'class': 'webhook_logger.slack.SlackHandler',
            'hook_url': 'https://my-super-hooks.com/12345',
            'formatter': 'slack_format',
        }
    },
    'loggers': {
        'dict_config': {
            'handlers': ['slack'],
            'level': 'DEBUG'
        }
    }
}


class TestSlackLogging(unittest.TestCase):
    def setUp(self):
        self.rm = requests_mock.mock()
        self.rm.start()

    def tearDown(self):
        self.rm.stop()

    def _build_logger(self, name, url=None, filter=False, formatter=False,
                      formatter_title=None):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        h = SlackHandler(hook_url=url)
        if filter:
            h.addFilter(SlackLogFilter())
        if formatter:
            h.formatter = SlackFormatter(formatter_title)
        h.setLevel(logging.DEBUG)
        logger.addHandler(h)
        return logger

    def test_incorrect_config(self):
        logger = self._build_logger('incorrect')
        logger.info("test")
        self.assertEqual(self.rm.call_count, 0)

    def test_correct_config(self):
        self.rm.post('https://some-hook.com/abcde', text='ok')
        logger = self._build_logger('basic', 'https://some-hook.com/abcde')
        logger.info("test")
        self.assertEqual(self.rm.call_count, 1)

    @mock.patch('webhook_logger.slack.settings')
    def test_django_config(self, settings):
        settings.SLACK_WEBHOOK_URL = 'https://some-hook.com/abcde'
        self.rm.post('https://some-hook.com/abcde', text='ok')
        logger = self._build_logger('django')
        logger.info("Test")
        self.assertEqual(self.rm.call_count, 1)
        self.assertEqual(self.rm.last_request.body.decode(), '{"text": "Test"}')

    def test_filtering_out(self):
        self.rm.post('https://some-hook.com/abcde', text='ok')
        logger = self._build_logger('filter_out', 'https://some-hook.com/abcde', filter=True)
        logger.info("test filtering")
        self.assertEqual(self.rm.call_count, 0)

    def test_filtering_in(self):
        self.rm.post('https://some-hook.com/abcde', text='ok')
        logger = self._build_logger('filter_in', 'https://some-hook.com/abcde', filter=True)
        logger.info("test filtering", extra={'notify_slack': True})
        self.assertEqual(self.rm.call_count, 1)
        self.assertEqual(self.rm.last_request.body.decode(), '{"text": "test filtering"}')

    def _assert_has_attachment(self, msg, color, title=None):
        actual = self.rm.last_request.body.decode()
        actual_dict = json.loads(actual)
        record = actual_dict["attachments"][0]
        self.assertEqual(record["text"], msg)
        self.assertEqual(record['title'], title)
        if color is None:
            self.assertNotIn("color", record)
        else:
            self.assertEqual(record["color"], color)
        self.assertIsNotNone(record['ts'])

    def test_formatter(self):
        self.rm.post('https://some-formatted-hook.com/xyz', text='ok')
        logger = self._build_logger('formatted_on',
                                    'https://some-formatted-hook.com/xyz',
                                    formatter=True,
                                    formatter_title='title')

        logger.debug("Test debugging")
        self._assert_has_attachment("Test debugging", None, 'title')

        logger.info("Test formatting")
        self._assert_has_attachment("Test formatting", "good", 'title')

        logger.warning("Test formatting")
        self._assert_has_attachment("Test formatting", "warning", 'title')

        logger.error("Test formatting")
        self._assert_has_attachment("Test formatting", "#E91E63", 'title')

        logger.critical("Test formatting")
        self._assert_has_attachment("Test formatting", "danger", 'title')

    def test_dict_config(self):
        dictConfig(DICT_CONFIG)
        logger = logging.getLogger('dict_config')
        self.rm.post('https://my-super-hooks.com/12345', text='ok')
        logger.info("Test without filter dictConfig")
        self.assertEqual(self.rm.call_count, 0)

        logger.info("Test with dictConfig", extra={'notify_slack': True})
        self.assertEqual(self.rm.call_count, 1)
        self._assert_has_attachment("Test with dictConfig", "good")

    @mock.patch('webhook_logger.slack.SlackHandler.handleError')
    def test_connection_error(self, error_handler):
        """Should call logging error handler when offline"""
        self.rm.post('https://some-hook.com/exception-log', exc=requests.ConnectionError)
        logger = self._build_logger('exception', 'https://some-hook.com/exception-log')
        logger.info("Testing when something fails on the wire")
        self.assertEqual(self.rm.call_count, 1)
        error_handler.assert_called_once()
