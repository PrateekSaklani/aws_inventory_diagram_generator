"""
EKS Resource Collector
"""

from typing import List
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.eks import EKSClient
from models.eks import EKSClusterModel, EKSNodeGroupModel

logger = get_logger(__name__)


class EKSCollector:
    """Collects EKS cluster and nodegroup resources."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.eks_client = EKSClient(session, region)

    def collect(self) -> List[EKSClusterModel]:
        """Collect all EKS clusters and their node groups."""
        logger.info(f"Collecting EKS resources in {self.region}")

        clusters = []
        cluster_names = self.eks_client.list_clusters()

        if not cluster_names:
            logger.info(f"No EKS clusters found in {self.region}")
            return clusters

        for cluster_name in cluster_names:
            raw_cluster = self.eks_client.describe_cluster(cluster_name)
            cluster = EKSClusterModel.from_aws_response(raw_cluster, self.region)

            # Collect node groups
            nodegroup_names = self.eks_client.list_nodegroups(cluster_name)
            for ng_name in nodegroup_names:
                raw_ng = self.eks_client.describe_nodegroup(cluster_name, ng_name)
                cluster.node_groups.append(
                    EKSNodeGroupModel.from_aws_response(raw_ng)
                )

            # Collect Fargate profiles
            fargate_names = self.eks_client.list_fargate_profiles(cluster_name)
            for fp_name in fargate_names:
                raw_fp = self.eks_client.describe_fargate_profile(cluster_name, fp_name)
                cluster.fargate_profiles.append({
                    "fargate_profile_name": raw_fp.get("fargateProfileName"),
                    "fargate_profile_arn": raw_fp.get("fargateProfileArn"),
                    "status": raw_fp.get("status"),
                    "subnets": raw_fp.get("subnets", []),
                    "selectors": raw_fp.get("selectors", []),
                })

            # Collect addons
            cluster.addons = self.eks_client.list_addons(cluster_name)

            clusters.append(cluster)

        logger.info(f"Collected {len(clusters)} EKS clusters in {self.region}")
        return clusters
