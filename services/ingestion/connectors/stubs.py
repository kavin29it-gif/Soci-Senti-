"""
Out-of-Scope Platform Connector Stubs (v2 Roadmap).
Provides clean BaseConnector-compliant interfaces raising NotImplementedError
with comprehensive documentation on required enterprise credentials and rate limits.
"""

from collections.abc import Iterator

from services.ingestion.connectors.base import BaseConnector
from services.ingestion.models import RawPost


class XConnector(BaseConnector):
    """
    Adapter for X (formerly Twitter) v2 API.
    # TODO(v2): Requires X Developer Portal Pro or Enterprise tier subscription.
    Required Credentials in .env:
      - X_API_KEY
      - X_API_SECRET
      - X_BEARER_TOKEN
      - X_CLIENT_ID
      - X_CLIENT_SECRET
    Rate Limits: 300 requests / 15-minute window per app on Pro tier.
    """

    def __init__(self, **kwargs):
        super().__init__(name="x", rate=0.33, capacity=5.0, **kwargs)

    def fetch(self, query_or_channel: str, limit: int = 100) -> Iterator[RawPost]:
        """# TODO(v2): Implement X v2 Search Stream / Recent Search API."""
        raise NotImplementedError(
            "# TODO(v2): X (Twitter) connector is out of scope for MVP (~60% scope). "
            "Please configure enterprise Bearer token credentials for v2 release."
        )


class InstagramConnector(BaseConnector):
    """
    Adapter for Meta Graph API / Instagram Graph API.
    # TODO(v2): Requires Facebook Developer App with Instagram Graph API permissions:
      - instagram_basic
      - instagram_manage_comments
      - Business Account Verification
    Required Credentials in .env:
      - META_APP_ID
      - META_APP_SECRET
      - INSTAGRAM_ACCESS_TOKEN
    Rate Limits: 200 calls / hour per user token.
    """

    def __init__(self, **kwargs):
        super().__init__(name="instagram", rate=0.05, capacity=2.0, **kwargs)

    def fetch(self, query_or_channel: str, limit: int = 100) -> Iterator[RawPost]:
        """# TODO(v2): Implement Instagram Graph API media search."""
        raise NotImplementedError(
            "# TODO(v2): Instagram connector is out of scope for MVP (~60% scope). "
            "Please configure verified Meta Developer App token for v2 release."
        )
