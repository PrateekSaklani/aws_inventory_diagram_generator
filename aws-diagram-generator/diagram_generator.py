#!/usr/bin/env python3
"""
AWS Architecture Diagram Generator

Generates architecture diagrams from inventory.json using the diagrams library.

Usage:
    python diagram_generator.py
    python diagram_generator.py --input output/inventory.json --output diagrams/architecture
"""

import argparse
import json
import os
from typing import Dict, Any, List

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2, ECS, EKS, Lambda
from diagrams.aws.database import RDS, ElastiCache, Aurora
from diagrams.aws.network import VPC, PublicSubnet, PrivateSubnet, NATGateway, InternetGateway, ELB, ALB, NLB, Route53
from diagrams.aws.general import GenericDatabase


def load_inventory(file_path: str) -> Dict[str, Any]:
    """Load inventory from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def get_resource_name(resource: Dict, default_key: str, fallback: str = "unnamed") -> str:
    """Get display name for a resource."""
    name = resource.get("name") or resource.get("tags", {}).get("Name")
    if name:
        return name[:30]  # Truncate long names
    return resource.get(default_key, fallback)[:30]


def generate_vpc_diagram(
    vpc_data: Dict[str, Any],
    ec2_instances: List[Dict],
    ecs_clusters: List[Dict],
    eks_clusters: List[Dict],
    rds_data: Dict[str, Any],
    elasticache_data: Dict[str, Any],
    load_balancers: Dict[str, Any],
    output_name: str,
    region: str
):
    """Generate diagram for a single VPC."""
    vpc_id = vpc_data["vpc_id"]
    vpc_name = get_resource_name(vpc_data, "vpc_id", vpc_id)

    # Filter resources by VPC
    vpc_ec2 = [i for i in ec2_instances if i.get("vpc_id") == vpc_id]
    vpc_rds_instances = [r for r in rds_data.get("instances", []) if r.get("vpc_id") == vpc_id]
    vpc_rds_clusters = [r for r in rds_data.get("clusters", []) if r.get("vpc_id") == vpc_id]
    vpc_elasticache = [c for c in elasticache_data.get("clusters", []) if c.get("cache_subnet_group_name")]
    vpc_repl_groups = elasticache_data.get("replication_groups", [])

    # Filter EKS clusters by VPC
    vpc_eks = [c for c in eks_clusters if c.get("vpc_id") == vpc_id]

    # Filter ECS by checking service subnets
    vpc_subnet_ids = {s["subnet_id"] for s in vpc_data.get("subnets", [])}
    vpc_ecs = []
    for cluster in ecs_clusters:
        for svc in cluster.get("services", []):
            if any(s in vpc_subnet_ids for s in svc.get("subnets", [])):
                vpc_ecs.append(cluster)
                break

    # Filter load balancers by VPC
    vpc_albs = [lb for lb in load_balancers.get("application_load_balancers", []) if lb.get("vpc_id") == vpc_id]
    vpc_nlbs = [lb for lb in load_balancers.get("network_load_balancers", []) if lb.get("vpc_id") == vpc_id]
    vpc_clbs = [lb for lb in load_balancers.get("classic_load_balancers", []) if lb.get("vpc_id") == vpc_id]

    # Group subnets by type (public/private)
    public_subnets = []
    private_subnets = []
    for subnet in vpc_data.get("subnets", []):
        subnet_name = get_resource_name(subnet, "subnet_id")
        if subnet.get("map_public_ip_on_launch") or "public" in subnet_name.lower() or "lb" in subnet_name.lower():
            public_subnets.append(subnet)
        else:
            private_subnets.append(subnet)

    graph_attr = {
        "fontsize": "20",
        "bgcolor": "white",
        "pad": "0.5",
        "splines": "spline",
    }

    with Diagram(
        f"AWS Architecture - {vpc_name}",
        filename=output_name,
        show=False,
        direction="TB",
        graph_attr=graph_attr,
    ):
        with Cluster(f"Region: {region}"):
            with Cluster(f"VPC: {vpc_name}\n{vpc_data['cidr_block']}"):

                # Internet Gateway
                igw_nodes = []
                for igw in vpc_data.get("internet_gateways", []):
                    igw_name = igw.get("tags", {}).get("Name", "IGW")
                    igw_nodes.append(InternetGateway(igw_name[:20]))

                # NAT Gateways
                nat_nodes = []
                for nat in vpc_data.get("nat_gateways", []):
                    if nat.get("state") == "available":
                        nat_name = nat.get("tags", {}).get("Name", "NAT")
                        nat_nodes.append(NATGateway(nat_name[:20]))

                # Public Subnets
                alb_nodes = []
                nlb_nodes = []
                if public_subnets or vpc_albs or vpc_nlbs:
                    with Cluster("Public Subnets"):
                        # ALBs
                        for alb in vpc_albs:
                            alb_name = alb.get("load_balancer_name", "ALB")[:25]
                            alb_nodes.append(ALB(alb_name))

                        # NLBs
                        for nlb in vpc_nlbs:
                            nlb_name = nlb.get("load_balancer_name", "NLB")[:25]
                            nlb_nodes.append(NLB(nlb_name))

                        # Classic LBs
                        for clb in vpc_clbs:
                            clb_name = clb.get("load_balancer_name", "CLB")[:25]
                            ELB(clb_name)

                # Private Subnets - Compute
                ec2_nodes = []
                ecs_nodes = []
                eks_nodes = []
                if private_subnets or vpc_ec2 or vpc_ecs or vpc_eks:
                    with Cluster("Private Subnets - Compute"):
                        # EC2 Instances (group by state)
                        running_ec2 = [i for i in vpc_ec2 if i.get("state") == "running"]
                        if running_ec2:
                            # Group similar instances
                            if len(running_ec2) <= 5:
                                for instance in running_ec2:
                                    name = get_resource_name(instance, "instance_id")
                                    ec2_nodes.append(EC2(name))
                            else:
                                ec2_nodes.append(EC2(f"EC2 x{len(running_ec2)}"))

                        # ECS Clusters
                        for cluster in vpc_ecs:
                            cluster_name = cluster.get("cluster_name", "ECS")[:25]
                            svc_count = len(cluster.get("services", []))
                            ecs_nodes.append(ECS(f"{cluster_name}\n({svc_count} services)"))

                        # EKS Clusters
                        for cluster in vpc_eks:
                            cluster_name = cluster.get("cluster_name", "EKS")[:25]
                            ng_count = len(cluster.get("node_groups", []))
                            eks_nodes.append(EKS(f"{cluster_name}\n({ng_count} node groups)"))

                # Private Subnets - Data
                rds_nodes = []
                cache_nodes = []
                if vpc_rds_instances or vpc_rds_clusters or vpc_elasticache or vpc_repl_groups:
                    with Cluster("Private Subnets - Data"):
                        # RDS Instances
                        for rds in vpc_rds_instances:
                            rds_name = rds.get("db_instance_identifier", "RDS")[:25]
                            engine = rds.get("engine", "")
                            if "aurora" in engine.lower():
                                rds_nodes.append(Aurora(f"{rds_name}\n{engine}"))
                            else:
                                rds_nodes.append(RDS(f"{rds_name}\n{engine}"))

                        # RDS Clusters (Aurora)
                        for cluster in vpc_rds_clusters:
                            cluster_name = cluster.get("db_cluster_identifier", "Aurora")[:25]
                            rds_nodes.append(Aurora(f"{cluster_name}\n(Aurora)"))

                        # ElastiCache
                        for cache in vpc_elasticache:
                            cache_name = cache.get("cache_cluster_id", "Cache")[:25]
                            engine = cache.get("engine", "redis")
                            cache_nodes.append(ElastiCache(f"{cache_name}\n{engine}"))

                        # Replication Groups
                        for rg in vpc_repl_groups:
                            rg_name = rg.get("replication_group_id", "Redis")[:25]
                            cache_nodes.append(ElastiCache(f"{rg_name}\n(Redis Cluster)"))

                # Draw connections
                # IGW -> ALBs
                for igw in igw_nodes:
                    for alb in alb_nodes:
                        igw >> Edge(color="darkgreen") >> alb
                    for nlb in nlb_nodes:
                        igw >> Edge(color="darkgreen") >> nlb

                # ALBs -> ECS/EKS/EC2
                for alb in alb_nodes:
                    for ecs in ecs_nodes:
                        alb >> Edge(color="blue") >> ecs
                    for eks in eks_nodes:
                        alb >> Edge(color="blue") >> eks
                    for ec2 in ec2_nodes[:3]:  # Limit connections
                        alb >> Edge(color="blue") >> ec2

                # NLBs -> ECS/EKS/EC2
                for nlb in nlb_nodes:
                    for ecs in ecs_nodes:
                        nlb >> Edge(color="orange") >> ecs
                    for eks in eks_nodes:
                        nlb >> Edge(color="orange") >> eks

                # Compute -> Data
                for ecs in ecs_nodes:
                    for rds in rds_nodes[:2]:
                        ecs >> Edge(color="purple", style="dashed") >> rds
                    for cache in cache_nodes[:2]:
                        ecs >> Edge(color="red", style="dashed") >> cache

                for eks in eks_nodes:
                    for rds in rds_nodes[:2]:
                        eks >> Edge(color="purple", style="dashed") >> rds
                    for cache in cache_nodes[:2]:
                        eks >> Edge(color="red", style="dashed") >> cache


def generate_overview_diagram(
    inventory: Dict[str, Any],
    output_name: str
):
    """Generate a high-level overview diagram of all regions."""
    graph_attr = {
        "fontsize": "24",
        "bgcolor": "white",
        "pad": "0.5",
    }

    with Diagram(
        f"AWS Architecture Overview - Account {inventory['metadata']['account_id']}",
        filename=output_name,
        show=False,
        direction="TB",
        graph_attr=graph_attr,
    ):
        for region_name, region_data in inventory.get("regions", {}).items():
            if "error" in region_data:
                continue

            with Cluster(f"Region: {region_name}"):
                vpcs = region_data.get("vpcs", [])
                ec2_count = len(region_data.get("ec2_instances", []))
                ecs_count = len(region_data.get("ecs_clusters", []))
                eks_count = len(region_data.get("eks_clusters", []))
                rds_count = len(region_data.get("rds", {}).get("instances", []))
                cache_count = len(region_data.get("elasticache", {}).get("clusters", []))
                lb_count = (
                    len(region_data.get("load_balancers", {}).get("application_load_balancers", [])) +
                    len(region_data.get("load_balancers", {}).get("network_load_balancers", []))
                )

                for vpc in vpcs:
                    vpc_name = get_resource_name(vpc, "vpc_id")
                    with Cluster(f"VPC: {vpc_name}"):
                        resources = []
                        if ec2_count > 0:
                            resources.append(EC2(f"EC2 x{ec2_count}"))
                        if ecs_count > 0:
                            resources.append(ECS(f"ECS x{ecs_count}"))
                        if eks_count > 0:
                            resources.append(EKS(f"EKS x{eks_count}"))
                        if rds_count > 0:
                            resources.append(RDS(f"RDS x{rds_count}"))
                        if cache_count > 0:
                            resources.append(ElastiCache(f"Cache x{cache_count}"))
                        if lb_count > 0:
                            resources.append(ALB(f"LB x{lb_count}"))

                        if not resources:
                            GenericDatabase("Empty VPC")


def main():
    parser = argparse.ArgumentParser(description="Generate AWS architecture diagrams")
    parser.add_argument(
        "--input",
        default="output/inventory.json",
        help="Path to inventory JSON file"
    )
    parser.add_argument(
        "--output",
        default="output/architecture",
        help="Output file path (without extension)"
    )
    parser.add_argument(
        "--vpc",
        help="Generate diagram for specific VPC ID only"
    )
    parser.add_argument(
        "--overview-only",
        action="store_true",
        help="Generate only the overview diagram"
    )
    args = parser.parse_args()

    # Load inventory
    print(f"Loading inventory from {args.input}...")
    inventory = load_inventory(args.input)

    # Create output directory
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate overview diagram
    print("Generating overview diagram...")
    generate_overview_diagram(inventory, f"{args.output}_overview")
    print(f"  Created: {args.output}_overview.png")

    if args.overview_only:
        return

    # Generate per-VPC diagrams
    for region_name, region_data in inventory.get("regions", {}).items():
        if "error" in region_data:
            print(f"Skipping {region_name} (error in data)")
            continue

        vpcs = region_data.get("vpcs", [])
        ec2_instances = region_data.get("ec2_instances", [])
        ecs_clusters = region_data.get("ecs_clusters", [])
        eks_clusters = region_data.get("eks_clusters", [])
        rds_data = region_data.get("rds", {})
        elasticache_data = region_data.get("elasticache", {})
        load_balancers = region_data.get("load_balancers", {})

        for vpc in vpcs:
            vpc_id = vpc["vpc_id"]

            # Skip if specific VPC requested and this isn't it
            if args.vpc and vpc_id != args.vpc:
                continue

            # Skip default VPCs with no resources
            if vpc.get("is_default"):
                vpc_subnet_ids = {s["subnet_id"] for s in vpc.get("subnets", [])}
                has_resources = any(
                    i.get("vpc_id") == vpc_id for i in ec2_instances
                ) or any(
                    c.get("vpc_id") == vpc_id for c in eks_clusters
                )
                if not has_resources:
                    print(f"Skipping default VPC {vpc_id} (no resources)")
                    continue

            vpc_name = get_resource_name(vpc, "vpc_id")
            safe_name = vpc_name.replace(" ", "_").replace("/", "_")
            output_file = f"{args.output}_{region_name}_{safe_name}"

            print(f"Generating diagram for VPC: {vpc_name} ({vpc_id})...")
            generate_vpc_diagram(
                vpc,
                ec2_instances,
                ecs_clusters,
                eks_clusters,
                rds_data,
                elasticache_data,
                load_balancers,
                output_file,
                region_name
            )
            print(f"  Created: {output_file}.png")

    print("\nDiagram generation complete!")


if __name__ == "__main__":
    main()
