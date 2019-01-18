# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import logging

import requests

try:
    from django.conf import settings
except ImportError:
    settings = None


class SlackHandler(logging.Handler):
    """Logging handler to post to Slack to the webhook URL"""

    def __init__(self, hook_url=None, *args, **kwargs):
        super(SlackHandler, self).__init__(*args, **kwargs)
        self._hook_url = hook_url
        self.formatter = SimpleSlackFormatter()

    @property
    def hook_url(self):
        if self._hook_url is None:
            self._hook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '')
        return self._hook_url

    def emit(self, record):
        """
        Submit the record with a POST request
        """
        try:
            slack_data = self.format(record)
            requests.post(self.hook_url, json=slack_data)
        except Exception:
            self.handleError(record)

    def filter(self, record):
        """
        Disable the logger if hook_url isn't defined,
        we don't want to do it in all environments (e.g local/CI)
        """
        if not self.hook_url:
            return 0
        return super(SlackHandler, self).filter(record)


class SlackLogFilter(logging.Filter):
    """
    Logging filter to decide when logging to Slack is requested, using
    the `extra` kwargs:

        `logger.info("...", extra={'notify_slack': True})`
    """

    def filter(self, record):
        return getattr(record, 'notify_slack', False)


class SimpleSlackFormatter(logging.Formatter):
    """Basic formatter without styling"""
    def format(self, record):
        return {'text': record.getMessage()}


class SlackFormatter(logging.Formatter):

    def __init__(self, title=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title

    def format(self, record):
        """
        Format message content, timestamp when it was logged and a
        coloured border depending on the severity of the message
        """
        ret = {
            'ts': record.created,
            'text': record.getMessage(),
            'title': self.title
        }
        try:
            loglevel_colour = {
                'INFO': 'good',
                'WARNING': 'warning',
                'ERROR': '#E91E63',
                'CRITICAL': 'danger',
            }
            ret['color'] = loglevel_colour[record.levelname]
        except KeyError:
            pass
        return {'attachments': [ret]}
