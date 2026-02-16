"""
ElastiCache (Redis/Memcached) Resource Collector
"""

from typing import Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.elasticache import ElastiCacheClient
from models.redis import ElastiCacheClusterModel, ReplicationGroupModel

logger = get_logger(__name__)


class RedisCollector:
    """Collects ElastiCache resources (Redis and Memcached)."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.elasticache_client = ElastiCacheClient(session, region)

    def collect(self) -> Dict[str, Any]:
        """Collect all ElastiCache clusters and replication groups."""
        logger.info(f"Collecting ElastiCache resources in {self.region}")

        result = {
            "clusters": [],
            "replication_groups": [],
            "serverless_caches": [],
        }

        # Collect cache clusters
        raw_clusters = self.elasticache_client.describe_cache_clusters()
        result["clusters"] = [
            ElastiCacheClusterModel.from_aws_response(c, self.region).to_dict()
            for c in raw_clusters
        ]

        # Collect replication groups (Redis clusters)
        raw_repl_groups = self.elasticache_client.describe_replication_groups()
        result["replication_groups"] = [
            ReplicationGroupModel.from_aws_response(rg, self.region).to_dict()
            for rg in raw_repl_groups
        ]

        # Collect serverless caches
        raw_serverless = self.elasticache_client.describe_serverless_caches()
        result["serverless_caches"] = [{
            "serverless_cache_name": sc.get("ServerlessCacheName"),
            "status": sc.get("Status"),
            "engine": sc.get("Engine"),
            "endpoint": sc.get("Endpoint", {}).get("Address"),
        } for sc in raw_serverless]

        logger.info(
            f"Collected {len(result['clusters'])} ElastiCache clusters and "
            f"{len(result['replication_groups'])} replication groups in {self.region}"
        )
        return result
