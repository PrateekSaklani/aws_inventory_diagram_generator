"""
Elastic Beanstalk Resource Collector
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.elasticbeanstalk import ElasticBeanstalkClient
from models.elasticbeanstalk import ElasticBeanstalkApplicationModel, ElasticBeanstalkEnvironmentModel

logger = get_logger(__name__)


class ElasticBeanstalkCollector:
    """Collects Elastic Beanstalk resources."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.eb_client = ElasticBeanstalkClient(session, region)

    def collect(self) -> Dict[str, Any]:
        """Collect all Elastic Beanstalk applications and environments."""
        logger.info(f"Collecting Elastic Beanstalk resources in {self.region}")

        result = {
            "applications": [],
            "environments": [],
        }

        # Collect applications
        raw_applications = self.eb_client.describe_applications()
        result["applications"] = [
            ElasticBeanstalkApplicationModel.from_aws_response(app).to_dict()
            for app in raw_applications
        ]

        # Collect environments
        raw_environments = self.eb_client.describe_environments()
        for env in raw_environments:
            env_model = ElasticBeanstalkEnvironmentModel.from_aws_response(env, self.region)

            # Get additional resources for the environment
            if env.get("EnvironmentId"):
                resources = self.eb_client.describe_environment_resources(env["EnvironmentId"])
                env_model.resources = {
                    "instances": [i.get("Id") for i in resources.get("Instances", [])],
                    "auto_scaling_groups": [a.get("Name") for a in resources.get("AutoScalingGroups", [])],
                    "load_balancers": [lb.get("Name") for lb in resources.get("LoadBalancers", [])],
                    "triggers": [t.get("Name") for t in resources.get("Triggers", [])],
                    "queues": [q.get("Name") for q in resources.get("Queues", [])],
                }

            result["environments"].append(env_model.to_dict())

        logger.info(
            f"Collected {len(result['applications'])} applications and "
            f"{len(result['environments'])} environments in {self.region}"
        )
        return result
