# C:\nxtturn\Loopline\tests\community\test_username_suggestions.py

import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

# Import the necessary fixtures from your conftest
from tests.conftest import user_factory, api_client_factory

# Mark all tests in this file to use the database
pytestmark = pytest.mark.django_db

User = get_user_model()


def test_username_available_returns_true(api_client_factory):
    """
    Verifies that a brand new username returns available: True.
    """
    client = api_client_factory()

    # We use the path registered in community/urls.py
    response = client.get("/api/check-username/", {"username": "brand_new_user_123"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["available"] is True
    assert response.data["suggestions"] == []


def test_existing_username_returns_taken_with_suggestions(
    user_factory, api_client_factory
):
    """
    Verifies that if a username is taken, the API returns available: False
    and exactly 3 unique suggestions.
    """
    # Create an existing user using your factory
    existing_username = "vinay_pro"
    user_factory(username=existing_username)

    client = api_client_factory()

    response = client.get("/api/check-username/", {"username": existing_username})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["available"] is False

    # Verify suggestions logic
    assert len(response.data["suggestions"]) == 3
    for suggestion in response.data["suggestions"]:
        assert existing_username in suggestion  # Suggestion should be based on input
        assert not User.objects.filter(
            username=suggestion
        ).exists()  # Suggestion must be actually free


def test_short_username_returns_not_available(api_client_factory):
    """
    Verifies that usernames under 3 characters are rejected immediately.
    """
    client = api_client_factory()

    response = client.get("/api/check-username/", {"username": "ab"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["available"] is False
    assert response.data["suggestions"] == []


def test_username_check_is_case_insensitive(user_factory, api_client_factory):
    """
    Verifies that 'Vinay' and 'vinay' are treated as the same account.
    """
    user_factory(username="Vinay")
    client = api_client_factory()

    response = client.get("/api/check-username/", {"username": "VINAY"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["available"] is False
