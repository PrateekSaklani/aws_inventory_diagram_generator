"""
Redshift Data Models
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class RedshiftClusterModel:
    """Represents a Redshift Cluster."""
    cluster_identifier: str
    cluster_arn: str
    node_type: str
    cluster_status: str
    region: str
    number_of_nodes: int = 1
    db_name: Optional[str] = None
    master_username: Optional[str] = None
    endpoint_address: Optional[str] = None
    endpoint_port: Optional[int] = None
    cluster_create_time: Optional[str] = None
    automated_snapshot_retention_period: int = 0
    cluster_security_groups: List[str] = field(default_factory=list)
    vpc_security_groups: List[str] = field(default_factory=list)
    vpc_id: Optional[str] = None
    cluster_subnet_group_name: Optional[str] = None
    availability_zone: Optional[str] = None
    publicly_accessible: bool = False
    encrypted: bool = False
    cluster_version: Optional[str] = None
    allow_version_upgrade: bool = True
    maintenance_track_name: Optional[str] = None
    elastic_resize_number_of_node_options: Optional[str] = None
    total_storage_capacity_in_mega_bytes: int = 0
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "RedshiftClusterModel":
        endpoint = data.get("Endpoint", {})
        vpc_sgs = data.get("VpcSecurityGroups", [])
        cluster_sgs = data.get("ClusterSecurityGroups", [])
        tags = data.get("Tags", [])

        return cls(
            cluster_identifier=data.get("ClusterIdentifier", ""),
            cluster_arn=data.get("ClusterNamespaceArn", ""),
            node_type=data.get("NodeType", ""),
            cluster_status=data.get("ClusterStatus", ""),
            region=region,
            number_of_nodes=data.get("NumberOfNodes", 1),
            db_name=data.get("DBName"),
            master_username=data.get("MasterUsername"),
            endpoint_address=endpoint.get("Address"),
            endpoint_port=endpoint.get("Port"),
            cluster_create_time=data.get("ClusterCreateTime").isoformat() if data.get("ClusterCreateTime") else None,
            automated_snapshot_retention_period=data.get("AutomatedSnapshotRetentionPeriod", 0),
            cluster_security_groups=[sg.get("ClusterSecurityGroupName") for sg in cluster_sgs],
            vpc_security_groups=[sg.get("VpcSecurityGroupId") for sg in vpc_sgs],
            vpc_id=data.get("VpcId"),
            cluster_subnet_group_name=data.get("ClusterSubnetGroupName"),
            availability_zone=data.get("AvailabilityZone"),
            publicly_accessible=data.get("PubliclyAccessible", False),
            encrypted=data.get("Encrypted", False),
            cluster_version=data.get("ClusterVersion"),
            allow_version_upgrade=data.get("AllowVersionUpgrade", True),
            maintenance_track_name=data.get("MaintenanceTrackName"),
            elastic_resize_number_of_node_options=data.get("ElasticResizeNumberOfNodeOptions"),
            total_storage_capacity_in_mega_bytes=data.get("TotalStorageCapacityInMegaBytes", 0),
            tags={t["Key"]: t["Value"] for t in tags} if tags else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RedshiftServerlessWorkgroupModel:
    """Represents a Redshift Serverless Workgroup."""
    workgroup_id: str
    workgroup_name: str
    workgroup_arn: str
    namespace_name: str
    region: str
    status: str
    base_capacity: int = 0
    enhanced_vpc_routing: bool = False
    publicly_accessible: bool = False
    endpoint_address: Optional[str] = None
    endpoint_port: Optional[int] = None
    vpc_id: Optional[str] = None
    subnet_ids: List[str] = field(default_factory=list)
    security_group_ids: List[str] = field(default_factory=list)
    creation_date: Optional[str] = None

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "RedshiftServerlessWorkgroupModel":
        endpoint = data.get("endpoint", {})
        vpc_endpoints = endpoint.get("vpcEndpoints", [{}])
        first_vpc_endpoint = vpc_endpoints[0] if vpc_endpoints else {}

        return cls(
            workgroup_id=data.get("workgroupId", ""),
            workgroup_name=data.get("workgroupName", ""),
            workgroup_arn=data.get("workgroupArn", ""),
            namespace_name=data.get("namespaceName", ""),
            region=region,
            status=data.get("status", ""),
            base_capacity=data.get("baseCapacity", 0),
            enhanced_vpc_routing=data.get("enhancedVpcRouting", False),
            publicly_accessible=data.get("publiclyAccessible", False),
            endpoint_address=endpoint.get("address"),
            endpoint_port=endpoint.get("port"),
            vpc_id=first_vpc_endpoint.get("vpcId"),
            subnet_ids=data.get("subnetIds", []),
            security_group_ids=data.get("securityGroupIds", []),
            creation_date=data.get("creationDate").isoformat() if data.get("creationDate") else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RedshiftServerlessNamespaceModel:
    """Represents a Redshift Serverless Namespace."""
    namespace_id: str
    namespace_name: str
    namespace_arn: str
    region: str
    status: str
    db_name: Optional[str] = None
    admin_username: Optional[str] = None
    creation_date: Optional[str] = None
    iam_roles: List[str] = field(default_factory=list)
    kms_key_id: Optional[str] = None
    log_exports: List[str] = field(default_factory=list)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "RedshiftServerlessNamespaceModel":
        return cls(
            namespace_id=data.get("namespaceId", ""),
            namespace_name=data.get("namespaceName", ""),
            namespace_arn=data.get("namespaceArn", ""),
            region=region,
            status=data.get("status", ""),
            db_name=data.get("dbName"),
            admin_username=data.get("adminUsername"),
            creation_date=data.get("creationDate").isoformat() if data.get("creationDate") else None,
            iam_roles=data.get("iamRoles", []),
            kms_key_id=data.get("kmsKeyId"),
            log_exports=data.get("logExports", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
