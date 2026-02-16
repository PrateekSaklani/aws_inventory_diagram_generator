"""
RDS Client - Read-only operations for RDS resources
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class RDSClient:
    """Wrapper for RDS boto3 client with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.client = session.get_client("rds", region)

    def describe_db_instances(self) -> List[Dict[str, Any]]:
        """Get all RDS DB instances."""
        instances = []
        paginator = self.client.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            instances.extend(page.get("DBInstances", []))
        logger.info(f"Found {len(instances)} RDS instances in {self.region}")
        return instances

    def describe_db_clusters(self) -> List[Dict[str, Any]]:
        """Get all RDS DB clusters (Aurora)."""
        clusters = []
        paginator = self.client.get_paginator("describe_db_clusters")
        for page in paginator.paginate():
            clusters.extend(page.get("DBClusters", []))
        logger.info(f"Found {len(clusters)} RDS clusters in {self.region}")
        return clusters

    def describe_db_subnet_groups(self) -> List[Dict[str, Any]]:
        """Get all DB subnet groups."""
        groups = []
        paginator = self.client.get_paginator("describe_db_subnet_groups")
        for page in paginator.paginate():
            groups.extend(page.get("DBSubnetGroups", []))
        return groups

    def describe_db_parameter_groups(self) -> List[Dict[str, Any]]:
        """Get all DB parameter groups."""
        groups = []
        paginator = self.client.get_paginator("describe_db_parameter_groups")
        for page in paginator.paginate():
            groups.extend(page.get("DBParameterGroups", []))
        return groups

    def describe_db_cluster_parameter_groups(self) -> List[Dict[str, Any]]:
        """Get all DB cluster parameter groups."""
        groups = []
        paginator = self.client.get_paginator("describe_db_cluster_parameter_groups")
        for page in paginator.paginate():
            groups.extend(page.get("DBClusterParameterGroups", []))
        return groups

    def describe_db_snapshots(self) -> List[Dict[str, Any]]:
        """Get all DB snapshots."""
        snapshots = []
        paginator = self.client.get_paginator("describe_db_snapshots")
        for page in paginator.paginate(SnapshotType="manual"):
            snapshots.extend(page.get("DBSnapshots", []))
        return snapshots

    def describe_db_cluster_snapshots(self) -> List[Dict[str, Any]]:
        """Get all DB cluster snapshots."""
        snapshots = []
        paginator = self.client.get_paginator("describe_db_cluster_snapshots")
        for page in paginator.paginate(SnapshotType="manual"):
            snapshots.extend(page.get("DBClusterSnapshots", []))
        return snapshots
