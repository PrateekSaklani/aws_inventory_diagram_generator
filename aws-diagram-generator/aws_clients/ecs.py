"""
ECS Client - Read-only operations for ECS resources
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class ECSClient:
    """Wrapper for ECS boto3 client with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.client = session.get_client("ecs", region)

    def list_clusters(self) -> List[str]:
        """Get all ECS cluster ARNs."""
        clusters = []
        paginator = self.client.get_paginator("list_clusters")
        for page in paginator.paginate():
            clusters.extend(page.get("clusterArns", []))
        logger.info(f"Found {len(clusters)} ECS clusters in {self.region}")
        return clusters

    def describe_clusters(self, cluster_arns: List[str]) -> List[Dict[str, Any]]:
        """Get detailed info for ECS clusters."""
        if not cluster_arns:
            return []

        # describe_clusters has a limit of 100 clusters per call
        all_clusters = []
        for i in range(0, len(cluster_arns), 100):
            batch = cluster_arns[i:i + 100]
            response = self.client.describe_clusters(
                clusters=batch,
                include=["ATTACHMENTS", "SETTINGS", "STATISTICS", "TAGS"]
            )
            all_clusters.extend(response.get("clusters", []))
        return all_clusters

    def list_services(self, cluster_arn: str) -> List[str]:
        """Get all service ARNs in a cluster."""
        services = []
        paginator = self.client.get_paginator("list_services")
        for page in paginator.paginate(cluster=cluster_arn):
            services.extend(page.get("serviceArns", []))
        return services

    def describe_services(self, cluster_arn: str, service_arns: List[str]) -> List[Dict[str, Any]]:
        """Get detailed info for ECS services."""
        if not service_arns:
            return []

        # describe_services has a limit of 10 services per call
        all_services = []
        for i in range(0, len(service_arns), 10):
            batch = service_arns[i:i + 10]
            response = self.client.describe_services(
                cluster=cluster_arn,
                services=batch,
                include=["TAGS"]
            )
            all_services.extend(response.get("services", []))
        return all_services

    def list_tasks(self, cluster_arn: str) -> List[str]:
        """Get all task ARNs in a cluster."""
        tasks = []
        paginator = self.client.get_paginator("list_tasks")
        for page in paginator.paginate(cluster=cluster_arn):
            tasks.extend(page.get("taskArns", []))
        return tasks

    def describe_tasks(self, cluster_arn: str, task_arns: List[str]) -> List[Dict[str, Any]]:
        """Get detailed info for ECS tasks."""
        if not task_arns:
            return []

        # describe_tasks has a limit of 100 tasks per call
        all_tasks = []
        for i in range(0, len(task_arns), 100):
            batch = task_arns[i:i + 100]
            response = self.client.describe_tasks(
                cluster=cluster_arn,
                tasks=batch,
                include=["TAGS"]
            )
            all_tasks.extend(response.get("tasks", []))
        return all_tasks

    def describe_task_definition(self, task_definition: str) -> Dict[str, Any]:
        """Get task definition details."""
        response = self.client.describe_task_definition(
            taskDefinition=task_definition,
            include=["TAGS"]
        )
        return response.get("taskDefinition", {})
