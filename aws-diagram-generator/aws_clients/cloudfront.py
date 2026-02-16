"""
AWS CloudFront Client

Read-only operations for CloudFront distributions.
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class CloudFrontClient:
    """Client for CloudFront read-only operations."""

    def __init__(self, session):
        self.client = session.get_client("cloudfront")

    def list_distributions(self) -> List[Dict[str, Any]]:
        """List all CloudFront distributions."""
        distributions = []

        try:
            paginator = self.client.get_paginator("list_distributions")
            for page in paginator.paginate():
                dist_list = page.get("DistributionList", {})
                items = dist_list.get("Items", [])

                for dist in items:
                    origins = []
                    for origin in dist.get("Origins", {}).get("Items", []):
                        origin_info = {
                            "id": origin.get("Id"),
                            "domain_name": origin.get("DomainName"),
                            "origin_path": origin.get("OriginPath", ""),
                        }
                        # Check if S3 or custom origin
                        if origin.get("S3OriginConfig"):
                            origin_info["type"] = "s3"
                        elif origin.get("CustomOriginConfig"):
                            origin_info["type"] = "custom"
                            origin_info["protocol_policy"] = origin.get("CustomOriginConfig", {}).get("OriginProtocolPolicy")
                        origins.append(origin_info)

                    # Get cache behaviors
                    cache_behaviors = []
                    default_cache = dist.get("DefaultCacheBehavior", {})
                    if default_cache:
                        cache_behaviors.append({
                            "path_pattern": "*",
                            "target_origin_id": default_cache.get("TargetOriginId"),
                            "viewer_protocol_policy": default_cache.get("ViewerProtocolPolicy"),
                            "allowed_methods": default_cache.get("AllowedMethods", {}).get("Items", []),
                            "compress": default_cache.get("Compress", False),
                        })

                    for cb in dist.get("CacheBehaviors", {}).get("Items", []):
                        cache_behaviors.append({
                            "path_pattern": cb.get("PathPattern"),
                            "target_origin_id": cb.get("TargetOriginId"),
                            "viewer_protocol_policy": cb.get("ViewerProtocolPolicy"),
                            "allowed_methods": cb.get("AllowedMethods", {}).get("Items", []),
                            "compress": cb.get("Compress", False),
                        })

                    # Get aliases (CNAMEs)
                    aliases = dist.get("Aliases", {}).get("Items", [])

                    distributions.append({
                        "id": dist.get("Id"),
                        "arn": dist.get("ARN"),
                        "domain_name": dist.get("DomainName"),
                        "status": dist.get("Status"),
                        "enabled": dist.get("Enabled"),
                        "aliases": aliases,
                        "origins": origins,
                        "cache_behaviors": cache_behaviors,
                        "price_class": dist.get("PriceClass"),
                        "http_version": dist.get("HttpVersion"),
                        "is_ipv6_enabled": dist.get("IsIPV6Enabled"),
                        "comment": dist.get("Comment", ""),
                        "web_acl_id": dist.get("WebACLId", ""),
                    })

            logger.info(f"Found {len(distributions)} CloudFront distributions")

        except Exception as e:
            logger.error(f"Failed to list CloudFront distributions: {e}")

        return distributions
