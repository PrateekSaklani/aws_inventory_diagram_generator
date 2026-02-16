"""
EKS Data Models
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class EKSNodeGroupModel:
    """Represents an EKS Node Group."""
    nodegroup_name: str
    nodegroup_arn: str
    cluster_name: str
    status: str
    capacity_type: Optional[str] = None
    instance_types: List[str] = field(default_factory=list)
    scaling_config: Dict[str, int] = field(default_factory=dict)
    subnets: List[str] = field(default_factory=list)
    ami_type: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any]) -> "EKSNodeGroupModel":
        return cls(
            nodegroup_name=data["nodegroupName"],
            nodegroup_arn=data["nodegroupArn"],
            cluster_name=data["clusterName"],
            status=data["status"],
            capacity_type=data.get("capacityType"),
            instance_types=data.get("instanceTypes", []),
            scaling_config=data.get("scalingConfig", {}),
            subnets=data.get("subnets", []),
            ami_type=data.get("amiType"),
            tags=data.get("tags", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EKSClusterModel:
    """Represents an EKS Cluster."""
    cluster_name: str
    cluster_arn: str
    status: str
    region: str
    version: str
    endpoint: Optional[str] = None
    role_arn: Optional[str] = None
    vpc_id: Optional[str] = None
    subnets: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    node_groups: List[EKSNodeGroupModel] = field(default_factory=list)
    fargate_profiles: List[Dict[str, Any]] = field(default_factory=list)
    addons: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "EKSClusterModel":
        vpc_config = data.get("resourcesVpcConfig", {})
        return cls(
            cluster_name=data["name"],
            cluster_arn=data["arn"],
            status=data["status"],
            region=region,
            version=data.get("version", ""),
            endpoint=data.get("endpoint"),
            role_arn=data.get("roleArn"),
            vpc_id=vpc_config.get("vpcId"),
            subnets=vpc_config.get("subnetIds", []),
            security_groups=vpc_config.get("securityGroupIds", []),
            tags=data.get("tags", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "cluster_name": self.cluster_name,
            "cluster_arn": self.cluster_arn,
            "status": self.status,
            "region": self.region,
            "version": self.version,
            "endpoint": self.endpoint,
            "role_arn": self.role_arn,
            "vpc_id": self.vpc_id,
            "subnets": self.subnets,
            "security_groups": self.security_groups,
            "node_groups": [ng.to_dict() for ng in self.node_groups],
            "fargate_profiles": self.fargate_profiles,
            "addons": self.addons,
            "tags": self.tags,
        }
        return result
