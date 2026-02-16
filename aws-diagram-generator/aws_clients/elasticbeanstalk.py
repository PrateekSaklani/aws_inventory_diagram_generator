"""
Elastic Beanstalk Client - Read-only operations for Elastic Beanstalk resources
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class ElasticBeanstalkClient:
    """Wrapper for Elastic Beanstalk boto3 client with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.client = session.get_client("elasticbeanstalk", region)

    def describe_applications(self) -> List[Dict[str, Any]]:
        """Get all Elastic Beanstalk applications."""
        response = self.client.describe_applications()
        applications = response.get("Applications", [])
        logger.info(f"Found {len(applications)} Elastic Beanstalk applications in {self.region}")
        return applications

    def describe_environments(self) -> List[Dict[str, Any]]:
        """Get all Elastic Beanstalk environments."""
        environments = []
        paginator = self.client.get_paginator("describe_environments")
        for page in paginator.paginate():
            environments.extend(page.get("Environments", []))
        logger.info(f"Found {len(environments)} Elastic Beanstalk environments in {self.region}")
        return environments

    def describe_environment_resources(self, environment_id: str) -> Dict[str, Any]:
        """Get resources for a specific environment."""
        try:
            response = self.client.describe_environment_resources(EnvironmentId=environment_id)
            return response.get("EnvironmentResources", {})
        except Exception as e:
            logger.warning(f"Failed to get resources for environment {environment_id}: {e}")
            return {}

    def describe_configuration_settings(self, application_name: str, environment_name: str) -> List[Dict[str, Any]]:
        """Get configuration settings for an environment."""
        try:
            response = self.client.describe_configuration_settings(
                ApplicationName=application_name,
                EnvironmentName=environment_name
            )
            return response.get("ConfigurationSettings", [])
        except Exception as e:
            logger.warning(f"Failed to get config for {environment_name}: {e}")
            return []

    def list_platform_versions(self) -> List[Dict[str, Any]]:
        """List available platform versions."""
        try:
            platforms = []
            paginator = self.client.get_paginator("list_platform_versions")
            for page in paginator.paginate():
                platforms.extend(page.get("PlatformSummaryList", []))
            return platforms
        except Exception as e:
            logger.warning(f"Failed to list platform versions: {e}")
            return []
