from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
import datetime

from .models import UserInput


class UtteranceModelTests(TestCase):
    def test_is_recent_with_future_time(self):
        """
        is_recent() returns False for future UserInput
        """
        future = timezone.now() + datetime.timedelta(days=30)
        future_user_input = UserInput(
            created_at=future, user_text='test')
        self.assertIs(future_user_input.is_recent(), False)

    def test_is_recent_with_old_UserInput(self):
        """
        is_recent() returns False for UserInputs whose time is older than 1 day
        """
        day_old = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_user_input = UserInput(
            created_at=day_old, user_text='test')
        self.assertIs(old_user_input.is_recent(), False)

    def test_is_recent_with_recent_user_input(self):
        """
        is_recent() returns True for UserInput whose time is within the last day
        """
        recent = timezone.now() - datetime.timedelta(hours=23, minutes=59)
        recent_user_input = UserInput(
            created_at=recent, user_text='test')
        self.assertIs(recent_user_input.is_recent(), True)
