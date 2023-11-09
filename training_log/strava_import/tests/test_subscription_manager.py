import os

import responses
from django.test import TestCase
from strava_import import strava_subscription_manager
from strava_import.models import StravaSubscription


class StravaAuthenticationTest(TestCase):
    def setUp(self):
        """Set up subscription parameters and strava client id and secret."""
        self.strava_client_id = "testclient"
        self.strava_client_secret = "testsecret"
        os.environ["STRAVA_CLIENT_ID"] = self.strava_client_id
        os.environ["STRAVA_CLIENT_SECRET"] = self.strava_client_secret

        self.subscription_id = 123
        self.callback_url = "http://localhost"
        self.application_id = 10
        self.resource_state = 1

    def create_strava_subscription(
        self,
        enabled=True,
        callback_url=None,
        state=StravaSubscription.SubscriptionState.VALIDATED,
        strava_id=None,
    ):
        """Create a strava subscription."""
        if callback_url is None:
            callback_url = self.callback_url
        if strava_id is None:
            strava_id = self.subscription_id
        strava_subscription = StravaSubscription.objects.create(
            enabled=enabled,
            callback_url=callback_url,
            state=state,
            strava_id=strava_id,
        )
        strava_subscription.save()
        return strava_subscription

    def mock_subscription_view(self):
        """Create a mock response for a subscription view request."""

        mock_response = [
            {
                "id": self.subscription_id,
                "resource_state": self.resource_state,
                "application_id": self.application_id,
                "callback_url": self.callback_url,
            }
        ]

        subscription_view_url = strava_subscription_manager.get_subscription_view_url()

        responses.add(
            responses.GET, subscription_view_url, json=mock_response, status=200
        )

    def test_get_subscription_view_url(self):
        """Test if the subscription view url is built correctly."""
        subscription_view_url = strava_subscription_manager.get_subscription_view_url()
        expected_url = (
            f"https://www.strava.com/api/v3/push_subscriptions"
            f"?client_id={self.strava_client_id}&client_secret={self.strava_client_secret}"
        )

        self.assertEqual(subscription_view_url, expected_url)

    @responses.activate
    def test_check_subscription(self):
        """If the subscription at strava is the same as our subscription,
        the subscription should stay enabled."""
        self.mock_subscription_view()
        self.create_strava_subscription()
        strava_subscription_manager.check_subscription()

        subscription = StravaSubscription.objects.get(strava_id=self.subscription_id)

        self.assertTrue(subscription.enabled)

    @responses.activate
    def test_disable_different_subscription(self):
        """If the subscription_id at strava is different than our subscription_id,
        the subscription should be disabled."""
        self.mock_subscription_view()
        different_subscription_id = self.subscription_id + 1
        self.create_strava_subscription(strava_id=different_subscription_id)
        strava_subscription_manager.check_subscription()

        subscription = StravaSubscription.objects.get(
            strava_id=different_subscription_id
        )

        self.assertFalse(subscription.enabled)

    @responses.activate
    def test_disable_different_callback_subscription(self):
        """If callback_url at strava is different than our callback_url,
        the subscription should be disabled."""
        self.mock_subscription_view()
        different_callback_url = "http://localhost2"
        self.create_strava_subscription(callback_url=different_callback_url)
        strava_subscription_manager.check_subscription()

        subscription = StravaSubscription.objects.get(strava_id=self.subscription_id)

        self.assertFalse(subscription.enabled)
