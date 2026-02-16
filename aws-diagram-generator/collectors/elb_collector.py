"""
ELB (Load Balancer) Resource Collector
"""

from typing import List, Dict, Any
from utils.aws_session import AWSSession
from utils.logger import get_logger
from aws_clients.elb import ELBClient

logger = get_logger(__name__)


class ELBCollector:
    """Collects Load Balancer resources (ALB, NLB, CLB)."""

    def __init__(self, session: AWSSession, region: str):
        self.session = session
        self.region = region
        self.elb_client = ELBClient(session, region)

    def collect(self) -> Dict[str, Any]:
        """Collect all load balancers and target groups."""
        logger.info(f"Collecting Load Balancer resources in {self.region}")

        result = {
            "application_load_balancers": [],
            "network_load_balancers": [],
            "classic_load_balancers": [],
            "target_groups": [],
        }

        # Collect ALB/NLB
        raw_lbs = self.elb_client.describe_load_balancers()
        for lb in raw_lbs:
            lb_data = self._simplify_load_balancer(lb)

            # Get listeners for each LB
            lb_data["listeners"] = self._collect_listeners(lb["LoadBalancerArn"])

            lb_type = lb.get("Type", "application")
            if lb_type == "application":
                result["application_load_balancers"].append(lb_data)
            elif lb_type == "network":
                result["network_load_balancers"].append(lb_data)

        # Collect Classic LBs
        raw_classic_lbs = self.elb_client.describe_classic_load_balancers()
        result["classic_load_balancers"] = [
            self._simplify_classic_load_balancer(lb)
            for lb in raw_classic_lbs
        ]

        # Collect target groups
        raw_target_groups = self.elb_client.describe_target_groups()
        result["target_groups"] = [
            self._simplify_target_group(tg)
            for tg in raw_target_groups
        ]

        logger.info(
            f"Collected {len(result['application_load_balancers'])} ALBs, "
            f"{len(result['network_load_balancers'])} NLBs, "
            f"{len(result['classic_load_balancers'])} CLBs in {self.region}"
        )
        return result

    def _simplify_load_balancer(self, lb: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify ALB/NLB data."""
        return {
            "load_balancer_name": lb["LoadBalancerName"],
            "load_balancer_arn": lb["LoadBalancerArn"],
            "dns_name": lb.get("DNSName"),
            "type": lb.get("Type"),
            "scheme": lb.get("Scheme"),
            "state": lb.get("State", {}).get("Code"),
            "vpc_id": lb.get("VpcId"),
            "availability_zones": [
                {
                    "zone_name": az.get("ZoneName"),
                    "subnet_id": az.get("SubnetId"),
                }
                for az in lb.get("AvailabilityZones", [])
            ],
            "security_groups": lb.get("SecurityGroups", []),
            "ip_address_type": lb.get("IpAddressType"),
            "region": self.region,
        }

    def _simplify_classic_load_balancer(self, lb: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify Classic LB data."""
        return {
            "load_balancer_name": lb["LoadBalancerName"],
            "dns_name": lb.get("DNSName"),
            "scheme": lb.get("Scheme"),
            "vpc_id": lb.get("VPCId"),
            "availability_zones": lb.get("AvailabilityZones", []),
            "subnets": lb.get("Subnets", []),
            "security_groups": lb.get("SecurityGroups", []),
            "instances": [i["InstanceId"] for i in lb.get("Instances", [])],
            "listeners": [
                {
                    "protocol": l.get("Protocol"),
                    "load_balancer_port": l.get("LoadBalancerPort"),
                    "instance_protocol": l.get("InstanceProtocol"),
                    "instance_port": l.get("InstancePort"),
                }
                for l in lb.get("ListenerDescriptions", [])
            ],
            "health_check": lb.get("HealthCheck", {}),
            "region": self.region,
        }

    def _simplify_target_group(self, tg: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify target group data."""
        return {
            "target_group_name": tg["TargetGroupName"],
            "target_group_arn": tg["TargetGroupArn"],
            "protocol": tg.get("Protocol"),
            "port": tg.get("Port"),
            "vpc_id": tg.get("VpcId"),
            "target_type": tg.get("TargetType"),
            "health_check_protocol": tg.get("HealthCheckProtocol"),
            "health_check_path": tg.get("HealthCheckPath"),
            "load_balancer_arns": tg.get("LoadBalancerArns", []),
            "region": self.region,
        }

    def _collect_listeners(self, load_balancer_arn: str) -> List[Dict[str, Any]]:
        """Collect listeners for a load balancer."""
        raw_listeners = self.elb_client.describe_listeners(load_balancer_arn)
        return [
            {
                "listener_arn": l["ListenerArn"],
                "port": l.get("Port"),
                "protocol": l.get("Protocol"),
                "ssl_policy": l.get("SslPolicy"),
                "default_actions": [
                    {
                        "type": a.get("Type"),
                        "target_group_arn": a.get("TargetGroupArn"),
                    }
                    for a in l.get("DefaultActions", [])
                ],
            }
            for l in raw_listeners
        ]
