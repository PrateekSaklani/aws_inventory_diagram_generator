"""
ElastiCache (Redis/Memcached) Data Models
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class ElastiCacheClusterModel:
    """Represents an ElastiCache Cluster."""
    cache_cluster_id: str
    cache_cluster_status: str
    engine: str
    engine_version: str
    region: str
    cache_node_type: Optional[str] = None
    num_cache_nodes: int = 0
    preferred_availability_zone: Optional[str] = None
    cache_subnet_group_name: Optional[str] = None
    security_groups: List[str] = field(default_factory=list)
    replication_group_id: Optional[str] = None
    cache_nodes: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "ElastiCacheClusterModel":
        sgs = data.get("SecurityGroups", [])
        nodes = data.get("CacheNodes", [])

        return cls(
            cache_cluster_id=data["CacheClusterId"],
            cache_cluster_status=data["CacheClusterStatus"],
            engine=data["Engine"],
            engine_version=data.get("EngineVersion", ""),
            region=region,
            cache_node_type=data.get("CacheNodeType"),
            num_cache_nodes=data.get("NumCacheNodes", 0),
            preferred_availability_zone=data.get("PreferredAvailabilityZone"),
            cache_subnet_group_name=data.get("CacheSubnetGroupName"),
            security_groups=[sg["SecurityGroupId"] for sg in sgs],
            replication_group_id=data.get("ReplicationGroupId"),
            cache_nodes=[{
                "cache_node_id": n.get("CacheNodeId"),
                "cache_node_status": n.get("CacheNodeStatus"),
                "endpoint": n.get("Endpoint", {}),
            } for n in nodes],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReplicationGroupModel:
    """Represents an ElastiCache Replication Group (Redis cluster mode)."""
    replication_group_id: str
    description: str
    status: str
    region: str
    automatic_failover: Optional[str] = None
    multi_az: Optional[str] = None
    cluster_enabled: bool = False
    cache_node_type: Optional[str] = None
    num_node_groups: int = 0
    num_cache_clusters: int = 0
    primary_endpoint: Optional[str] = None
    reader_endpoint: Optional[str] = None
    node_groups: List[Dict[str, Any]] = field(default_factory=list)
    member_clusters: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_aws_response(cls, data: Dict[str, Any], region: str) -> "ReplicationGroupModel":
        primary_ep = data.get("ConfigurationEndpoint", {}) or data.get("NodeGroups", [{}])[0].get("PrimaryEndpoint", {})
        reader_ep = data.get("NodeGroups", [{}])[0].get("ReaderEndpoint", {}) if data.get("NodeGroups") else {}

        return cls(
            replication_group_id=data["ReplicationGroupId"],
            description=data.get("Description", ""),
            status=data["Status"],
            region=region,
            automatic_failover=data.get("AutomaticFailover"),
            multi_az=data.get("MultiAZ"),
            cluster_enabled=data.get("ClusterEnabled", False),
            cache_node_type=data.get("CacheNodeType"),
            num_node_groups=len(data.get("NodeGroups", [])),
            num_cache_clusters=len(data.get("MemberClusters", [])),
            primary_endpoint=primary_ep.get("Address") if primary_ep else None,
            reader_endpoint=reader_ep.get("Address") if reader_ep else None,
            node_groups=[{
                "node_group_id": ng.get("NodeGroupId"),
                "status": ng.get("Status"),
                "slots": ng.get("Slots"),
                "primary_endpoint": ng.get("PrimaryEndpoint", {}).get("Address"),
            } for ng in data.get("NodeGroups", [])],
            member_clusters=data.get("MemberClusters", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
