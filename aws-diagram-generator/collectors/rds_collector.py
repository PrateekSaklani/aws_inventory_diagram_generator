"""
RDS Resource Collector
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.rds import RDSClient
from models.rds import RDSInstanceModel, RDSClusterModel

logger = get_logger(__name__)


class RDSCollector:
    """Collects RDS database resources."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.rds_client = RDSClient(session, region)

    def collect(self) -> Dict[str, Any]:
        """Collect all RDS instances and clusters."""
        logger.info(f"Collecting RDS resources in {self.region}")

        result = {
            "instances": [],
            "clusters": [],
        }

        # Collect RDS instances
        raw_instances = self.rds_client.describe_db_instances()
        result["instances"] = [
            RDSInstanceModel.from_aws_response(i, self.region).to_dict()
            for i in raw_instances
        ]

        # Collect Aurora clusters
        raw_clusters = self.rds_client.describe_db_clusters()
        result["clusters"] = [
            RDSClusterModel.from_aws_response(c, self.region).to_dict()
            for c in raw_clusters
        ]

        logger.info(
            f"Collected {len(result['instances'])} RDS instances and "
            f"{len(result['clusters'])} clusters in {self.region}"
        )
        return result
