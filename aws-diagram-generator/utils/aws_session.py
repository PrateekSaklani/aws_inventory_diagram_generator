"""
AWS Session Manager - Handles boto3 session creation and role assumption
"""

import boto3
from botocore.config import Config
from typing import Optional, Dict, Any

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class AWSSession:
    """Manages AWS boto3 sessions and client creation with optional role assumption."""

    def __init__(
        self,
        profile: Optional[str] = None,
        region: Optional[str] = None,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        role_session_name: Optional[str] = None,
    ):
        self.profile = profile or config.AWS_PROFILE
        self.region = region
        self.role_arn = role_arn or config.ROLE_ARN
        self.external_id = external_id or config.EXTERNAL_ID
        self.role_session_name = role_session_name or config.ROLE_SESSION_NAME
        self._session = None
        self._assumed_credentials = None
        self._config = Config(
            retries={"max_attempts": 3, "mode": "standard"}
        )

    def _get_base_session(self) -> boto3.Session:
        """Get the base boto3 session (before role assumption)."""
        if self.profile:
            return boto3.Session(
                profile_name=self.profile,
                region_name=self.region
            )
        return boto3.Session(region_name=self.region)

    def _assume_role(self) -> Dict[str, Any]:
        """Assume the configured IAM role and return credentials."""
        if self._assumed_credentials:
            return self._assumed_credentials

        logger.info(f"Assuming role: {self.role_arn}")
        base_session = self._get_base_session()
        sts = base_session.client("sts")

        assume_role_params = {
            "RoleArn": self.role_arn,
            "RoleSessionName": self.role_session_name,
            "DurationSeconds": 3600,  # 1 hour
        }

        if self.external_id:
            assume_role_params["ExternalId"] = self.external_id

        response = sts.assume_role(**assume_role_params)
        self._assumed_credentials = response["Credentials"]

        logger.info(f"Successfully assumed role. Session expires: {self._assumed_credentials['Expiration']}")
        return self._assumed_credentials

    @property
    def session(self) -> boto3.Session:
        """Get or create boto3 session (with assumed role if configured)."""
        if self._session is None:
            if self.role_arn:
                credentials = self._assume_role()
                self._session = boto3.Session(
                    aws_access_key_id=credentials["AccessKeyId"],
                    aws_secret_access_key=credentials["SecretAccessKey"],
                    aws_session_token=credentials["SessionToken"],
                    region_name=self.region
                )
            else:
                self._session = self._get_base_session()
        return self._session

    def get_client(self, service_name: str, region: Optional[str] = None):
        """Create a boto3 client for the specified service."""
        region = region or self.region
        logger.debug(f"Creating {service_name} client for region {region}")
        return self.session.client(
            service_name,
            region_name=region,
            config=self._config
        )

    def get_resource(self, service_name: str, region: Optional[str] = None):
        """Create a boto3 resource for the specified service."""
        region = region or self.region
        return self.session.resource(
            service_name,
            region_name=region,
            config=self._config
        )

    def get_account_id(self) -> str:
        """Get the current AWS account ID."""
        sts = self.get_client("sts")
        identity = sts.get_caller_identity()
        logger.info(f"Caller ARN: {identity['Arn']}")
        return identity["Account"]

    def get_caller_identity(self) -> Dict[str, str]:
        """Get full caller identity (Account, Arn, UserId)."""
        sts = self.get_client("sts")
        return sts.get_caller_identity()

    def get_available_regions(self, service_name: str = "ec2") -> list:
        """Get list of available regions for a service."""
        return self.session.get_available_regions(service_name)
