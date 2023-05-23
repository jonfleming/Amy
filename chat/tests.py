from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
import datetime
import pytest
import unittest
from unittest import mock

from .models import UserInput

from .views import summary
from .views import transcript
from .views import homepage
from .views import register_request
from .views import login_request
from .views import logout_request
from .views import password_reset_request
from .views import send_reset_mail
from .views import session
from .forms import NewUserForm


class UserInputModelTests(TestCase):
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

class SummaryTest(unittest.TestCase):

    def test_summary_renders_correctly(self):
        response = summary(None)
        self.assertIn('Fleming AI', response.content.decode('utf-8'))

@pytest.mark.django_db
class TranscriptTest(unittest.TestCase):

    def test_transcript_gets_correct_queryset(self):
        self.request = mock.Mock()
        self.request.user = mock.Mock()
        self.request.user.username = 'test_user'
        queryset = transcript.get_queryset(self)
        self.assertEqual(queryset.count(), 0)


class HomepageTest(unittest.TestCase):

    def test_homepage_redirects_if_user_is_logged_in(self):
        request = mock.Mock()
        request.user = mock.Mock()
        request.user.is_authenticated = True
        response = homepage(request)
        self.assertEqual(response.status_code, 302)


class RegisterRequestTest(unittest.TestCase):

    def test_register_request_saves_user_correctly(self):
        request = mock.Mock()
        form = NewUserForm(request.POST)
        form.is_valid()
        register_request_view = register_request.as_view()
        response = register_request_view(request)
        self.assertEqual(response.status_code, 302)

@pytest.mark.django_db
class LoginRequestTest(unittest.TestCase):

    def test_login_request_logs_user_in_correctly(self):
        request = mock.Mock()
        request.method = 'POST'
        request.POST = mock.Mock()
        request.POST.username = 'test_user'
        request.POST.password = 'test_password'
        response = login_request(request)
        self.assertEqual(response.status_code, 302)


class LogoutRequestTest(unittest.TestCase):

    def test_logout_request_logs_user_out_correctly(self):
        request = mock.Mock()
        response = logout_request(request)
        self.assertEqual(response.status_code, 302)


class PasswordResetRequestTest(unittest.TestCase):

    def test_password_reset_request_sends_email_correctly(self):
        request = mock.Mock()
        request.POST = mock.Mock()
        request.POST.email = 'test_user@example.com'
        response = password_reset_request(request)
        self.assertEqual(response.status_code, 200)


class SendResetMailTest(unittest.TestCase):

    def test_send_reset_mail_sends_email_correctly(self):
        request = mock.Mock()
        user = mock.Mock()
        user.email = 'test_user@example.com'
        user.email_field = 'email'
        user.pk = 1
        user.name = 'test_user'
        send_reset_mail(request, user)
        self.assertEqual(len(user.email_messages), 1)


class SessionTest(unittest.TestCase):

    def test_session_gets_correct_response(self):
        request = unittest.mock.Mock()
        request.user = unittest.mock.Mock()
        request.user.username = 'test_user'
        session_view = session.as_view()
        response = session_view(request)
        self.assertEqual(response.status_code, 200)
