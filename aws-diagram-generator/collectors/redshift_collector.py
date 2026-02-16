"""
Redshift Resource Collector
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.redshift import RedshiftClient
from models.redshift import (
    RedshiftClusterModel,
    RedshiftServerlessWorkgroupModel,
    RedshiftServerlessNamespaceModel
)

logger = get_logger(__name__)


class RedshiftCollector:
    """Collects Redshift resources."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.redshift_client = RedshiftClient(session, region)

    def collect(self) -> Dict[str, Any]:
        """Collect all Redshift clusters and serverless resources."""
        logger.info(f"Collecting Redshift resources in {self.region}")

        result = {
            "clusters": [],
            "serverless_workgroups": [],
            "serverless_namespaces": [],
        }

        # Collect Redshift clusters
        raw_clusters = self.redshift_client.describe_clusters()
        result["clusters"] = [
            RedshiftClusterModel.from_aws_response(c, self.region).to_dict()
            for c in raw_clusters
        ]

        # Collect Redshift Serverless workgroups
        raw_workgroups = self.redshift_client.describe_serverless_workgroups()
        result["serverless_workgroups"] = [
            RedshiftServerlessWorkgroupModel.from_aws_response(w, self.region).to_dict()
            for w in raw_workgroups
        ]

        # Collect Redshift Serverless namespaces
        raw_namespaces = self.redshift_client.describe_serverless_namespaces()
        result["serverless_namespaces"] = [
            RedshiftServerlessNamespaceModel.from_aws_response(n, self.region).to_dict()
            for n in raw_namespaces
        ]

        logger.info(
            f"Collected {len(result['clusters'])} Redshift clusters, "
            f"{len(result['serverless_workgroups'])} serverless workgroups in {self.region}"
        )
        return result
