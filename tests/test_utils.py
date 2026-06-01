# coding: utf-8
"""Tests utils.py shared helpers."""
from dio_chacon_wifi_api.utils import redact_url
from yarl import URL


def test_redact_url_masks_credentials() -> None:
    """The redacted URL masks the credentials and keeps the non sensitive service name visible."""

    url = URL("wss://host/ws?email=toto@toto.com&password=DUMMY_PASS&serviceName=test_client&sessionToken=r:abc123")
    redacted = redact_url(url)

    assert "toto@toto.com" not in redacted
    assert "DUMMY_PASS" not in redacted
    assert "r:abc123" not in redacted
    assert "email=***" in redacted
    assert "password=***" in redacted
    assert "sessionToken=***" in redacted
    assert "serviceName=test_client" in redacted


def test_redact_url_without_sensitive_query_returns_url_unchanged() -> None:
    """A URL without any sensitive query parameter is returned unchanged."""

    url = URL("https://host/api?serviceName=test_client&page=1")
    redacted = redact_url(url)

    assert redacted == "https://host/api?serviceName=test_client&page=1"


def test_redact_url_without_query_returns_url_unchanged() -> None:
    """A URL without any query parameter is returned unchanged."""

    url = URL("https://host/api")
    redacted = redact_url(url)

    assert redacted == "https://host/api"


def test_redact_url_masks_only_present_sensitive_keys() -> None:
    """Only the sensitive keys that are present in the URL are masked."""

    url = URL("wss://host/ws?email=toto@toto.com&serviceName=test_client")
    redacted = redact_url(url)

    assert "toto@toto.com" not in redacted
    assert "email=***" in redacted
    assert "password" not in redacted
    assert "sessionToken" not in redacted
    assert "serviceName=test_client" in redacted
