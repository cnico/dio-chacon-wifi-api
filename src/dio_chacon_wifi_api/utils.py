# -*- coding: utf-8 -*-
"""Utility helpers shared across the DIO Chacon wifi API modules."""
from yarl import URL


SENSITIVE_QUERY_KEYS = ("email", "password", "sessionToken")


def redact_url(url: URL) -> str:
    """Returns the URL as a string with sensitive query parameters masked."""
    redactions = {key: "***" for key in SENSITIVE_QUERY_KEYS if key in url.query}
    return str(url.update_query(redactions))
