"""
RDS Data Models
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class RDSInstanceModel:
    """Represents an RDS DB Instance."""
    db_instance_identifier: str
    db_instance_arn: str
    db_instance_class: str
    engine: str
    engine_version: str
    status: str
    region: str
    allocated_storage: int
    storage_type: Optional[str] = None
    multi_az: bool = False
    publicly_accessible: bool = False
    vpc_id: Optional[str] = None
    db_subnet_group: Optional[str] = None
    availability_zone: Optional[str] = None
    endpoint_address: Optional[str] = None
    endpoint_port: Optional[int] = None
    security_groups: List[str] = field(default_factory=list)
    db_cluster_identifier: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "RDSInstanceModel":
        endpoint = data.get("Endpoint", {})
        subnet_group = data.get("DBSubnetGroup", {})
        vpc_sgs = data.get("VpcSecurityGroups", [])
        tags = data.get("TagList", [])

        return cls(
            db_instance_identifier=data["DBInstanceIdentifier"],
            db_instance_arn=data["DBInstanceArn"],
            db_instance_class=data["DBInstanceClass"],
            engine=data["Engine"],
            engine_version=data.get("EngineVersion", ""),
            status=data["DBInstanceStatus"],
            region=region,
            allocated_storage=data.get("AllocatedStorage", 0),
            storage_type=data.get("StorageType"),
            multi_az=data.get("MultiAZ", False),
            publicly_accessible=data.get("PubliclyAccessible", False),
            vpc_id=subnet_group.get("VpcId"),
            db_subnet_group=subnet_group.get("DBSubnetGroupName"),
            availability_zone=data.get("AvailabilityZone"),
            endpoint_address=endpoint.get("Address"),
            endpoint_port=endpoint.get("Port"),
            security_groups=[sg["VpcSecurityGroupId"] for sg in vpc_sgs],
            db_cluster_identifier=data.get("DBClusterIdentifier"),
            tags={t["Key"]: t["Value"] for t in tags} if tags else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RDSClusterModel:
    """Represents an RDS DB Cluster (Aurora)."""
    db_cluster_identifier: str
    db_cluster_arn: str
    engine: str
    engine_version: str
    status: str
    region: str
    engine_mode: Optional[str] = None
    allocated_storage: int = 0
    multi_az: bool = False
    vpc_id: Optional[str] = None
    db_subnet_group: Optional[str] = None
    availability_zones: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None
    reader_endpoint: Optional[str] = None
    port: Optional[int] = None
    security_groups: List[str] = field(default_factory=list)
    cluster_members: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "RDSClusterModel":
        vpc_sgs = data.get("VpcSecurityGroups", [])
        members = data.get("DBClusterMembers", [])
        tags = data.get("TagList", [])

        return cls(
            db_cluster_identifier=data["DBClusterIdentifier"],
            db_cluster_arn=data["DBClusterArn"],
            engine=data["Engine"],
            engine_version=data.get("EngineVersion", ""),
            status=data["Status"],
            region=region,
            engine_mode=data.get("EngineMode"),
            allocated_storage=data.get("AllocatedStorage", 0),
            multi_az=data.get("MultiAZ", False),
            vpc_id=data.get("VpcId"),
            db_subnet_group=data.get("DBSubnetGroup"),
            availability_zones=data.get("AvailabilityZones", []),
            endpoint=data.get("Endpoint"),
            reader_endpoint=data.get("ReaderEndpoint"),
            port=data.get("Port"),
            security_groups=[sg["VpcSecurityGroupId"] for sg in vpc_sgs],
            cluster_members=[m["DBInstanceIdentifier"] for m in members],
            tags={t["Key"]: t["Value"] for t in tags} if tags else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
