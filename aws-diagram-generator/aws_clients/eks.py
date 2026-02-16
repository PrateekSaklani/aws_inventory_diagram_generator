"""
EKS Client - Read-only operations for EKS resources
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class EKSClient:
    """Wrapper for EKS boto3 client with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.client = session.get_client("eks", region)

    def list_clusters(self) -> List[str]:
        """Get all EKS cluster names."""
        clusters = []
        paginator = self.client.get_paginator("list_clusters")
        for page in paginator.paginate():
            clusters.extend(page.get("clusters", []))
        logger.info(f"Found {len(clusters)} EKS clusters in {self.region}")
        return clusters

    def describe_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Get detailed info for an EKS cluster."""
        response = self.client.describe_cluster(name=cluster_name)
        return response.get("cluster", {})

    def list_nodegroups(self, cluster_name: str) -> List[str]:
        """Get all node group names in a cluster."""
        nodegroups = []
        paginator = self.client.get_paginator("list_nodegroups")
        for page in paginator.paginate(clusterName=cluster_name):
            nodegroups.extend(page.get("nodegroups", []))
        return nodegroups

    def describe_nodegroup(self, cluster_name: str, nodegroup_name: str) -> Dict[str, Any]:
        """Get detailed info for a node group."""
        response = self.client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name
        )
        return response.get("nodegroup", {})

    def list_fargate_profiles(self, cluster_name: str) -> List[str]:
        """Get all Fargate profile names in a cluster."""
        profiles = []
        paginator = self.client.get_paginator("list_fargate_profiles")
        for page in paginator.paginate(clusterName=cluster_name):
            profiles.extend(page.get("fargateProfileNames", []))
        return profiles

    def describe_fargate_profile(self, cluster_name: str, profile_name: str) -> Dict[str, Any]:
        """Get detailed info for a Fargate profile."""
        response = self.client.describe_fargate_profile(
            clusterName=cluster_name,
            fargateProfileName=profile_name
        )
        return response.get("fargateProfile", {})

    def list_addons(self, cluster_name: str) -> List[str]:
        """Get all addon names in a cluster."""
        addons = []
        paginator = self.client.get_paginator("list_addons")
        for page in paginator.paginate(clusterName=cluster_name):
            addons.extend(page.get("addons", []))
        return addons

    def describe_addon(self, cluster_name: str, addon_name: str) -> Dict[str, Any]:
        """Get detailed info for an addon."""
        response = self.client.describe_addon(
            clusterName=cluster_name,
            addonName=addon_name
        )
        return response.get("addon", {})
