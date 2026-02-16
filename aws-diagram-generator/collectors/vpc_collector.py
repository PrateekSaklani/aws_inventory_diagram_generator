"""
VPC Resource Collector
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.ec2 import EC2Client
from models.vpc import VPCModel, SubnetModel

logger = get_logger(__name__)


class VPCCollector:
    """Collects VPC and related networking resources."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.ec2_client = EC2Client(session, region)

    def collect(self) -> List[VPCModel]:
        """Collect all VPCs and their associated resources."""
        logger.info(f"Collecting VPCs in {self.region}")

        vpcs = []
        raw_vpcs = self.ec2_client.describe_vpcs()

        for raw_vpc in raw_vpcs:
            vpc = VPCModel.from_aws_response(raw_vpc, self.region)
            vpc_id = vpc.vpc_id

            # Collect associated resources
            vpc.subnets = [
                SubnetModel.from_aws_response(s)
                for s in self.ec2_client.describe_subnets(vpc_id)
            ]
            vpc.internet_gateways = self._simplify_igws(
                self.ec2_client.describe_internet_gateways(vpc_id)
            )
            vpc.nat_gateways = self._simplify_nat_gws(
                self.ec2_client.describe_nat_gateways(vpc_id)
            )
            vpc.route_tables = self._simplify_route_tables(
                self.ec2_client.describe_route_tables(vpc_id)
            )
            vpc.security_groups = self._simplify_security_groups(
                self.ec2_client.describe_security_groups(vpc_id)
            )
            vpc.vpc_endpoints = self._simplify_vpc_endpoints(
                self.ec2_client.describe_vpc_endpoints(vpc_id)
            )

            vpcs.append(vpc)

        logger.info(f"Collected {len(vpcs)} VPCs in {self.region}")
        return vpcs

    def collect_ec2_instances(self) -> List[Dict[str, Any]]:
        """Collect all EC2 instances in the region."""
        logger.info(f"Collecting EC2 instances in {self.region}")
        instances = self.ec2_client.describe_instances()
        return self._simplify_ec2_instances(instances)

    def _simplify_igws(self, igws: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplify internet gateway data."""
        return [{
            "internet_gateway_id": igw["InternetGatewayId"],
            "attachments": igw.get("Attachments", []),
            "tags": {t["Key"]: t["Value"] for t in igw.get("Tags", [])},
        } for igw in igws]

    def _simplify_nat_gws(self, nats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplify NAT gateway data."""
        return [{
            "nat_gateway_id": nat["NatGatewayId"],
            "state": nat.get("State"),
            "subnet_id": nat.get("SubnetId"),
            "connectivity_type": nat.get("ConnectivityType"),
            "public_ip": next(
                (addr.get("PublicIp") for addr in nat.get("NatGatewayAddresses", [])),
                None
            ),
            "tags": {t["Key"]: t["Value"] for t in nat.get("Tags", [])},
        } for nat in nats]

    def _simplify_route_tables(self, rts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplify route table data."""
        return [{
            "route_table_id": rt["RouteTableId"],
            "vpc_id": rt["VpcId"],
            "associations": [{
                "subnet_id": a.get("SubnetId"),
                "main": a.get("Main", False),
            } for a in rt.get("Associations", [])],
            "routes": [{
                "destination": r.get("DestinationCidrBlock") or r.get("DestinationIpv6CidrBlock"),
                "gateway_id": r.get("GatewayId"),
                "nat_gateway_id": r.get("NatGatewayId"),
                "state": r.get("State"),
            } for r in rt.get("Routes", [])],
            "tags": {t["Key"]: t["Value"] for t in rt.get("Tags", [])},
        } for rt in rts]

    def _simplify_security_groups(self, sgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplify security group data."""
        return [{
            "group_id": sg["GroupId"],
            "group_name": sg["GroupName"],
            "description": sg.get("Description"),
            "vpc_id": sg.get("VpcId"),
            "ingress_rules_count": len(sg.get("IpPermissions", [])),
            "egress_rules_count": len(sg.get("IpPermissionsEgress", [])),
            "tags": {t["Key"]: t["Value"] for t in sg.get("Tags", [])},
        } for sg in sgs]

    def _simplify_vpc_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplify VPC endpoint data."""
        return [{
            "vpc_endpoint_id": ep["VpcEndpointId"],
            "vpc_endpoint_type": ep.get("VpcEndpointType"),
            "service_name": ep.get("ServiceName"),
            "state": ep.get("State"),
            "subnet_ids": ep.get("SubnetIds", []),
            "tags": {t["Key"]: t["Value"] for t in ep.get("Tags", [])},
        } for ep in endpoints]

    def _simplify_ec2_instances(self, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplify EC2 instance data."""
        return [{
            "instance_id": i["InstanceId"],
            "instance_type": i.get("InstanceType"),
            "state": i.get("State", {}).get("Name"),
            "vpc_id": i.get("VpcId"),
            "subnet_id": i.get("SubnetId"),
            "private_ip": i.get("PrivateIpAddress"),
            "public_ip": i.get("PublicIpAddress"),
            "availability_zone": i.get("Placement", {}).get("AvailabilityZone"),
            "security_groups": [sg["GroupId"] for sg in i.get("SecurityGroups", [])],
            "tags": {t["Key"]: t["Value"] for t in i.get("Tags", [])},
            "name": next(
                (t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"),
                None
            ),
        } for i in instances]
