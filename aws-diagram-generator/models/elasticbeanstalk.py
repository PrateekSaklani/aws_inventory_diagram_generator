"""
Elastic Beanstalk Data Models
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ElasticBeanstalkApplicationModel:
    """Represents an Elastic Beanstalk Application."""
    application_name: str
    application_arn: str
    description: Optional[str] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    versions: List[str] = field(default_factory=list)
    configuration_templates: List[str] = field(default_factory=list)
    resource_lifecycle_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any]) -> "ElasticBeanstalkApplicationModel":
        return cls(
            application_name=data.get("ApplicationName", ""),
            application_arn=data.get("ApplicationArn", ""),
            description=data.get("Description"),
            date_created=data.get("DateCreated").isoformat() if data.get("DateCreated") else None,
            date_updated=data.get("DateUpdated").isoformat() if data.get("DateUpdated") else None,
            versions=data.get("Versions", []),
            configuration_templates=data.get("ConfigurationTemplates", []),
            resource_lifecycle_config=data.get("ResourceLifecycleConfig", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ElasticBeanstalkEnvironmentModel:
    """Represents an Elastic Beanstalk Environment."""
    environment_id: str
    environment_name: str
    environment_arn: str
    application_name: str
    region: str
    status: str
    health: str
    health_status: Optional[str] = None
    solution_stack_name: Optional[str] = None
    platform_arn: Optional[str] = None
    version_label: Optional[str] = None
    tier_name: Optional[str] = None
    tier_type: Optional[str] = None
    cname: Optional[str] = None
    endpoint_url: Optional[str] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    resources: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "ElasticBeanstalkEnvironmentModel":
        tier = data.get("Tier", {})
        resources = data.get("Resources", {})

        return cls(
            environment_id=data.get("EnvironmentId", ""),
            environment_name=data.get("EnvironmentName", ""),
            environment_arn=data.get("EnvironmentArn", ""),
            application_name=data.get("ApplicationName", ""),
            region=region,
            status=data.get("Status", ""),
            health=data.get("Health", ""),
            health_status=data.get("HealthStatus"),
            solution_stack_name=data.get("SolutionStackName"),
            platform_arn=data.get("PlatformArn"),
            version_label=data.get("VersionLabel"),
            tier_name=tier.get("Name"),
            tier_type=tier.get("Type"),
            cname=data.get("CNAME"),
            endpoint_url=data.get("EndpointURL"),
            date_created=data.get("DateCreated").isoformat() if data.get("DateCreated") else None,
            date_updated=data.get("DateUpdated").isoformat() if data.get("DateUpdated") else None,
            resources=resources,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
