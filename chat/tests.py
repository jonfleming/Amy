from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
import datetime

from .models import Utterance


class UtteranceModelTests(TestCase):
    def test_is_recent_with_future_time(self):
        """
        is_recent() returns False for future utterances
        """
        future = timezone.now() + datetime.timedelta(days=30)
        future_utterance = Utterance(
            utterance_time=future, utterance_text='test')
        self.assertIs(future_utterance.is_recent(), False)

    def test_is_recent_with_old_utterance(self):
        """
        is_recent() returns False for utterances whose time is older than 1 day
        """
        day_old = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_utterance = Utterance(
            utterance_time=day_old, utterance_text='test')
        self.assertIs(old_utterance.is_recent(), False)

    def test_is_recent_with_recent_utterance(self):
        """
        is_recent() returns True for utterances whose time is within the last day
        """
        recent = timezone.now() - datetime.timedelta(hours=23, minutes=59)
        recent_utterance = Utterance(
            utterance_time=recent, utterance_text='test')
        self.assertIs(recent_utterance.is_recent(), True)
