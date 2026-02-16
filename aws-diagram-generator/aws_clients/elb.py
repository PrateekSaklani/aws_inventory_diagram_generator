"""
ELB Client - Read-only operations for Load Balancer resources
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger

logger = get_logger(__name__)


class ELBClient:
    """Wrapper for ELB/ELBv2 boto3 clients with read-only operations."""

    def __init__(self, session: AWSSession, region: str):
        self.region = region
        self.elbv2_client = session.get_client("elbv2", region)
        self.elb_client = session.get_client("elb", region)

    def describe_load_balancers(self) -> List[Dict[str, Any]]:
        """Get all Application and Network Load Balancers."""
        lbs = []
        paginator = self.elbv2_client.get_paginator("describe_load_balancers")
        for page in paginator.paginate():
            lbs.extend(page.get("LoadBalancers", []))
        logger.info(f"Found {len(lbs)} ALB/NLB load balancers in {self.region}")
        return lbs

    def describe_classic_load_balancers(self) -> List[Dict[str, Any]]:
        """Get all Classic Load Balancers."""
        lbs = []
        paginator = self.elb_client.get_paginator("describe_load_balancers")
        for page in paginator.paginate():
            lbs.extend(page.get("LoadBalancerDescriptions", []))
        logger.info(f"Found {len(lbs)} Classic load balancers in {self.region}")
        return lbs

    def describe_target_groups(self) -> List[Dict[str, Any]]:
        """Get all target groups."""
        tgs = []
        paginator = self.elbv2_client.get_paginator("describe_target_groups")
        for page in paginator.paginate():
            tgs.extend(page.get("TargetGroups", []))
        return tgs

    def describe_listeners(self, load_balancer_arn: str) -> List[Dict[str, Any]]:
        """Get all listeners for a load balancer."""
        listeners = []
        paginator = self.elbv2_client.get_paginator("describe_listeners")
        for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
            listeners.extend(page.get("Listeners", []))
        return listeners

    def describe_rules(self, listener_arn: str) -> List[Dict[str, Any]]:
        """Get all rules for a listener."""
        rules = []
        paginator = self.elbv2_client.get_paginator("describe_rules")
        for page in paginator.paginate(ListenerArn=listener_arn):
            rules.extend(page.get("Rules", []))
        return rules

    def describe_target_health(self, target_group_arn: str) -> List[Dict[str, Any]]:
        """Get health status of targets in a target group."""
        response = self.elbv2_client.describe_target_health(
            TargetGroupArn=target_group_arn
        )
        return response.get("TargetHealthDescriptions", [])

    def describe_load_balancer_attributes(self, load_balancer_arn: str) -> List[Dict[str, Any]]:
        """Get attributes for a load balancer."""
        response = self.elbv2_client.describe_load_balancer_attributes(
            LoadBalancerArn=load_balancer_arn
        )
        return response.get("Attributes", [])
