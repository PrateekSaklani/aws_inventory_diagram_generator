"""
ECS Data Models
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class ECSServiceModel:
    """Represents an ECS Service."""
    service_name: str
    service_arn: str
    cluster_arn: str
    status: str
    desired_count: int
    running_count: int
    pending_count: int
    launch_type: Optional[str] = None
    task_definition: Optional[str] = None
    load_balancers: List[Dict[str, Any]] = field(default_factory=list)
    subnets: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any]) -> "ECSServiceModel":
        network_config = data.get("networkConfiguration", {}).get("awsvpcConfiguration", {})
        tags = data.get("tags", [])
        return cls(
            service_name=data["serviceName"],
            service_arn=data["serviceArn"],
            cluster_arn=data["clusterArn"],
            status=data["status"],
            desired_count=data.get("desiredCount", 0),
            running_count=data.get("runningCount", 0),
            pending_count=data.get("pendingCount", 0),
            launch_type=data.get("launchType"),
            task_definition=data.get("taskDefinition"),
            load_balancers=data.get("loadBalancers", []),
            subnets=network_config.get("subnets", []),
            security_groups=network_config.get("securityGroups", []),
            tags={t["key"]: t["value"] for t in tags} if tags else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ECSClusterModel:
    """Represents an ECS Cluster."""
    cluster_name: str
    cluster_arn: str
    status: str
    region: str
    registered_container_instances_count: int = 0
    running_tasks_count: int = 0
    pending_tasks_count: int = 0
    active_services_count: int = 0
    capacity_providers: List[str] = field(default_factory=list)
    services: List[ECSServiceModel] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "ECSClusterModel":
        tags = data.get("tags", [])
        return cls(
            cluster_name=data["clusterName"],
            cluster_arn=data["clusterArn"],
            status=data["status"],
            region=region,
            registered_container_instances_count=data.get("registeredContainerInstancesCount", 0),
            running_tasks_count=data.get("runningTasksCount", 0),
            pending_tasks_count=data.get("pendingTasksCount", 0),
            active_services_count=data.get("activeServicesCount", 0),
            capacity_providers=data.get("capacityProviders", []),
            tags={t["key"]: t["value"] for t in tags} if tags else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "cluster_name": self.cluster_name,
            "cluster_arn": self.cluster_arn,
            "status": self.status,
            "region": self.region,
            "registered_container_instances_count": self.registered_container_instances_count,
            "running_tasks_count": self.running_tasks_count,
            "pending_tasks_count": self.pending_tasks_count,
            "active_services_count": self.active_services_count,
            "capacity_providers": self.capacity_providers,
            "services": [s.to_dict() for s in self.services],
            "tags": self.tags,
        }
        return result
