"""
ElastiCache Client - Read-only operations for ElastiCache resources
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class ElastiCacheClient:
    """Wrapper for ElastiCache boto3 client with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.client = session.get_client("elasticache", region)

    def describe_cache_clusters(self) -> List[Dict[str, Any]]:
        """Get all ElastiCache clusters."""
        clusters = []
        paginator = self.client.get_paginator("describe_cache_clusters")
        for page in paginator.paginate(ShowCacheNodeInfo=True):
            clusters.extend(page.get("CacheClusters", []))
        logger.info(f"Found {len(clusters)} ElastiCache clusters in {self.region}")
        return clusters

    def describe_replication_groups(self) -> List[Dict[str, Any]]:
        """Get all ElastiCache replication groups (Redis clusters)."""
        groups = []
        paginator = self.client.get_paginator("describe_replication_groups")
        for page in paginator.paginate():
            groups.extend(page.get("ReplicationGroups", []))
        logger.info(f"Found {len(groups)} replication groups in {self.region}")
        return groups

    def describe_cache_subnet_groups(self) -> List[Dict[str, Any]]:
        """Get all cache subnet groups."""
        groups = []
        paginator = self.client.get_paginator("describe_cache_subnet_groups")
        for page in paginator.paginate():
            groups.extend(page.get("CacheSubnetGroups", []))
        return groups

    def describe_cache_parameter_groups(self) -> List[Dict[str, Any]]:
        """Get all cache parameter groups."""
        groups = []
        paginator = self.client.get_paginator("describe_cache_parameter_groups")
        for page in paginator.paginate():
            groups.extend(page.get("CacheParameterGroups", []))
        return groups

    def describe_serverless_caches(self) -> List[Dict[str, Any]]:
        """Get all serverless caches."""
        caches = []
        try:
            paginator = self.client.get_paginator("describe_serverless_caches")
            for page in paginator.paginate():
                caches.extend(page.get("ServerlessCaches", []))
        except self.client.exceptions.ClientError as e:
            # Serverless caches might not be available in all regions
            logger.debug(f"Serverless caches not available: {e}")
        return caches
