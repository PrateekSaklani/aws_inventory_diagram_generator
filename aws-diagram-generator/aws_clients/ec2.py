"""
EC2 Client - Read-only operations for EC2 and VPC resources
"""

from typing import List, Dict, Any, Optional
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class EC2Client:
    """Wrapper for EC2 boto3 client with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.client = session.get_client("ec2", region)

    def describe_vpcs(self) -> List[Dict[str, Any]]:
        """Get all VPCs in the region."""
        vpcs = []
        paginator = self.client.get_paginator("describe_vpcs")
        for page in paginator.paginate():
            vpcs.extend(page.get("Vpcs", []))
        logger.info(f"Found {len(vpcs)} VPCs in {self.region}")
        return vpcs

    def describe_subnets(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all subnets, optionally filtered by VPC."""
        subnets = []
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_subnets")
        for page in paginator.paginate(Filters=filters):
            subnets.extend(page.get("Subnets", []))
        return subnets

    def describe_instances(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all EC2 instances, optionally filtered by VPC."""
        instances = []
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_instances")
        for page in paginator.paginate(Filters=filters):
            for reservation in page.get("Reservations", []):
                instances.extend(reservation.get("Instances", []))
        logger.info(f"Found {len(instances)} EC2 instances in {self.region}")
        return instances

    def describe_security_groups(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all security groups, optionally filtered by VPC."""
        sgs = []
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_security_groups")
        for page in paginator.paginate(Filters=filters):
            sgs.extend(page.get("SecurityGroups", []))
        return sgs

    def describe_internet_gateways(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all internet gateways, optionally filtered by VPC."""
        igws = []
        filters = []
        if vpc_id:
            filters.append({"Name": "attachment.vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_internet_gateways")
        for page in paginator.paginate(Filters=filters):
            igws.extend(page.get("InternetGateways", []))
        return igws

    def describe_nat_gateways(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all NAT gateways, optionally filtered by VPC."""
        nats = []
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_nat_gateways")
        for page in paginator.paginate(Filters=filters):
            nats.extend(page.get("NatGateways", []))
        return nats

    def describe_route_tables(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all route tables, optionally filtered by VPC."""
        rts = []
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_route_tables")
        for page in paginator.paginate(Filters=filters):
            rts.extend(page.get("RouteTables", []))
        return rts

    def describe_network_acls(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all network ACLs, optionally filtered by VPC."""
        nacls = []
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_network_acls")
        for page in paginator.paginate(Filters=filters):
            nacls.extend(page.get("NetworkAcls", []))
        return nacls

    def describe_vpc_endpoints(self, vpc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all VPC endpoints, optionally filtered by VPC."""
        endpoints = []
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})

        paginator = self.client.get_paginator("describe_vpc_endpoints")
        for page in paginator.paginate(Filters=filters):
            endpoints.extend(page.get("VpcEndpoints", []))
        return endpoints
