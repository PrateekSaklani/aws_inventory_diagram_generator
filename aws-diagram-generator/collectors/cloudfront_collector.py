"""
CloudFront Collector

Collects CloudFront distribution information.
Note: CloudFront is a global service, not region-specific.
"""

from typing import Dict, Any
from aws_clients.cloudfront import CloudFrontClient
from utils.logger import get_logger

logger = get_logger(__name__)


class CloudFrontCollector:
    """Collector for CloudFront distributions."""

    def __init__(self, session):
        self.client = CloudFrontClient(session)

    def collect(self) -> Dict[str, Any]:
        """Collect all CloudFront distributions."""
        logger.info("Collecting CloudFront distributions (global)")

        distributions = self.client.list_distributions()

        logger.info(f"Collected {len(distributions)} CloudFront distributions")

        return {
            "distributions": distributions
        }
