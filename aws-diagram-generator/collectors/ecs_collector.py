"""
ECS Resource Collector
"""

from typing import List
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.ecs import ECSClient
from models.ecs import ECSClusterModel, ECSServiceModel

logger = get_logger(__name__)


class ECSCollector:
    """Collects ECS cluster and service resources."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.ecs_client = ECSClient(session, region)

    def collect(self) -> List[ECSClusterModel]:
        """Collect all ECS clusters and their services."""
        logger.info(f"Collecting ECS resources in {self.region}")

        clusters = []
        cluster_arns = self.ecs_client.list_clusters()

        if not cluster_arns:
            logger.info(f"No ECS clusters found in {self.region}")
            return clusters

        raw_clusters = self.ecs_client.describe_clusters(cluster_arns)

        for raw_cluster in raw_clusters:
            cluster = ECSClusterModel.from_aws_response(raw_cluster, self.region)

            # Collect services for this cluster
            service_arns = self.ecs_client.list_services(cluster.cluster_arn)
            if service_arns:
                raw_services = self.ecs_client.describe_services(
                    cluster.cluster_arn, service_arns
                )
                cluster.services = [
                    ECSServiceModel.from_aws_response(s)
                    for s in raw_services
                ]

            clusters.append(cluster)

        logger.info(f"Collected {len(clusters)} ECS clusters in {self.region}")
        return clusters
