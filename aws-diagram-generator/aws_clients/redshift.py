"""
Redshift Client - Read-only operations for Redshift resources
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class RedshiftClient:
    """Wrapper for Redshift boto3 client with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.client = session.get_client("redshift", region)
        self.serverless_client = session.get_client("redshift-serverless", region)

    def describe_clusters(self) -> List[Dict[str, Any]]:
        """Get all Redshift clusters."""
        clusters = []
        paginator = self.client.get_paginator("describe_clusters")
        for page in paginator.paginate():
            clusters.extend(page.get("Clusters", []))
        logger.info(f"Found {len(clusters)} Redshift clusters in {self.region}")
        return clusters

    def describe_cluster_subnet_groups(self) -> List[Dict[str, Any]]:
        """Get all Redshift subnet groups."""
        groups = []
        paginator = self.client.get_paginator("describe_cluster_subnet_groups")
        for page in paginator.paginate():
            groups.extend(page.get("ClusterSubnetGroups", []))
        return groups

    def describe_cluster_parameter_groups(self) -> List[Dict[str, Any]]:
        """Get all Redshift parameter groups."""
        groups = []
        paginator = self.client.get_paginator("describe_cluster_parameter_groups")
        for page in paginator.paginate():
            groups.extend(page.get("ParameterGroups", []))
        return groups

    def describe_cluster_snapshots(self, cluster_identifier: str = None) -> List[Dict[str, Any]]:
        """Get Redshift snapshots."""
        snapshots = []
        paginator = self.client.get_paginator("describe_cluster_snapshots")
        params = {"SnapshotType": "manual"}
        if cluster_identifier:
            params["ClusterIdentifier"] = cluster_identifier
        for page in paginator.paginate(**params):
            snapshots.extend(page.get("Snapshots", []))
        return snapshots

    def describe_serverless_workgroups(self) -> List[Dict[str, Any]]:
        """Get all Redshift Serverless workgroups."""
        try:
            workgroups = []
            paginator = self.serverless_client.get_paginator("list_workgroups")
            for page in paginator.paginate():
                workgroups.extend(page.get("workgroups", []))
            logger.info(f"Found {len(workgroups)} Redshift Serverless workgroups in {self.region}")
            return workgroups
        except Exception as e:
            logger.warning(f"Failed to list Redshift Serverless workgroups: {e}")
            return []

    def describe_serverless_namespaces(self) -> List[Dict[str, Any]]:
        """Get all Redshift Serverless namespaces."""
        try:
            namespaces = []
            paginator = self.serverless_client.get_paginator("list_namespaces")
            for page in paginator.paginate():
                namespaces.extend(page.get("namespaces", []))
            logger.info(f"Found {len(namespaces)} Redshift Serverless namespaces in {self.region}")
            return namespaces
        except Exception as e:
            logger.warning(f"Failed to list Redshift Serverless namespaces: {e}")
            return []
