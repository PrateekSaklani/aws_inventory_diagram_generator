"""
VPC and Subnet Data Models
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


def get_name_from_tags(tags: List[Dict[str, str]]) -> Optional[str]:
    """Extract Name tag from AWS tags list."""
    if not tags:
        return None
    for tag in tags:
        if tag.get("Key") == "Name":
            return tag.get("Value")
    return None


@dataclass
class SubnetModel:
    """Represents an AWS Subnet."""
    subnet_id: str
    vpc_id: str
    cidr_block: str
    availability_zone: str
    availability_zone_id: str
    state: str
    map_public_ip_on_launch: bool
    name: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any]) -> "SubnetModel":
        tags = data.get("Tags", [])
        return cls(
            subnet_id=data["SubnetId"],
            vpc_id=data["VpcId"],
            cidr_block=data["CidrBlock"],
            availability_zone=data["AvailabilityZone"],
            availability_zone_id=data["AvailabilityZoneId"],
            state=data["State"],
            map_public_ip_on_launch=data.get("MapPublicIpOnLaunch", False),
            name=get_name_from_tags(tags),
            tags={t["Key"]: t["Value"] for t in tags} if tags else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VPCModel:
    """Represents an AWS VPC."""
    vpc_id: str
    cidr_block: str
    state: str
    is_default: bool
    region: str
    name: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    subnets: List[SubnetModel] = field(default_factory=list)
    internet_gateways: List[Dict[str, Any]] = field(default_factory=list)
    nat_gateways: List[Dict[str, Any]] = field(default_factory=list)
    route_tables: List[Dict[str, Any]] = field(default_factory=list)
    security_groups: List[Dict[str, Any]] = field(default_factory=list)
    vpc_endpoints: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "VPCModel":
        tags = data.get("Tags", [])
        return cls(
            vpc_id=data["VpcId"],
            cidr_block=data["CidrBlock"],
            state=data["State"],
            is_default=data.get("IsDefault", False),
            region=region,
            name=get_name_from_tags(tags),
            tags={t["Key"]: t["Value"] for t in tags} if tags else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "vpc_id": self.vpc_id,
            "cidr_block": self.cidr_block,
            "state": self.state,
            "is_default": self.is_default,
            "region": self.region,
            "name": self.name,
            "tags": self.tags,
            "subnets": [s.to_dict() for s in self.subnets],
            "internet_gateways": self.internet_gateways,
            "nat_gateways": self.nat_gateways,
            "route_tables": self.route_tables,
            "security_groups": self.security_groups,
            "vpc_endpoints": self.vpc_endpoints,
        }
        return result
