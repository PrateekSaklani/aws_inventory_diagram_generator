#!/usr/bin/env python3
"""
AWS Architecture Diagram Generator - Detailed View

Generates detailed architecture diagrams showing:
- ECS services with task definitions
- EKS clusters with node groups
- EC2 instances grouped by role (standalone, ECS, EKS)

Usage:
    python diagram_generator_detailed.py --vpc vpc-06c8ff336a2ff2c2b
"""

import argparse
import json
import os
import re
from typing import Dict, Any, List, Set

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import (
    EC2, ECS, EKS, EC2Instances,
    ElasticContainerServiceService, ElasticContainerServiceTask, Fargate,
    ElasticBeanstalk
)
from diagrams.aws.database import RDS, ElastiCache, Aurora, Redshift
from diagrams.aws.network import (
    VPC, NATGateway, InternetGateway,
    ELB, ALB, NLB, Route53
)
from diagrams.aws.integration import SQS
from diagrams.aws.storage import S3
from diagrams.generic.compute import Rack
from diagrams.onprem.container import Docker
from diagrams.onprem.queue import RabbitMQ
from diagrams.onprem.database import Cassandra
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Service


def load_inventory(file_path: str) -> Dict[str, Any]:
    """Load inventory from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def load_k8s_workloads(file_path: str) -> Dict[str, Any]:
    """Load K8s workloads from JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_resource_name(resource: Dict, default_key: str, fallback: str = "unnamed") -> str:
    """Get display name for a resource."""
    name = resource.get("name") or resource.get("tags", {}).get("Name")
    if name:
        return name[:35]
    return resource.get(default_key, fallback)[:35]


def format_label(name: str, max_len: int = 20, max_lines: int = 2) -> str:
    """Format label to prevent overlaps - truncate and wrap."""
    if len(name) <= max_len:
        return name
    # Truncate with ellipsis
    return name[:max_len-2] + ".."


def format_multiline_label(*parts, max_len: int = 22) -> str:
    """Format multiple parts into a clean multiline label."""
    formatted = []
    for part in parts:
        if part:
            part_str = str(part)
            if len(part_str) > max_len:
                part_str = part_str[:max_len-2] + ".."
            formatted.append(part_str)
    return "\n".join(formatted)


def extract_service_name(task_def_arn: str) -> str:
    """Extract service name from task definition ARN."""
    if not task_def_arn:
        return "unknown"
    # arn:aws:ecs:region:account:task-definition/name:revision
    match = re.search(r'task-definition/([^:]+)', task_def_arn)
    if match:
        return match.group(1)
    return task_def_arn.split('/')[-1].split(':')[0]


def categorize_ec2_instances(
    ec2_instances: List[Dict],
    ecs_clusters: List[Dict],
    eks_clusters: List[Dict]
) -> Dict[str, List[Dict]]:
    """Categorize EC2 instances into standalone, ECS, and EKS."""

    # Get EKS node group instance patterns
    eks_patterns = set()
    for cluster in eks_clusters:
        cluster_name = cluster.get("cluster_name", "")
        eks_patterns.add(cluster_name.lower())
        for ng in cluster.get("node_groups", []):
            ng_name = ng.get("nodegroup_name", "")
            eks_patterns.add(ng_name.lower())

    # Get ECS cluster names
    ecs_patterns = set()
    for cluster in ecs_clusters:
        ecs_patterns.add(cluster.get("cluster_name", "").lower())

    categorized = {
        "standalone": [],
        "ecs": [],
        "eks": []
    }

    for instance in ec2_instances:
        if instance.get("state") != "running":
            continue

        tags = instance.get("tags", {})
        name = instance.get("name", "").lower()
        all_tags = " ".join(f"{k}={v}" for k, v in tags.items()).lower()

        # Check for EKS indicators
        is_eks = (
            "kubernetes.io" in all_tags or
            "eks" in all_tags or
            "karpenter" in all_tags or
            any(p in name or p in all_tags for p in eks_patterns if p)
        )

        # Check for ECS indicators
        is_ecs = (
            "ecs" in all_tags or
            "ecs:cluster" in all_tags or
            any(p in name for p in ecs_patterns if p)
        )

        if is_eks:
            categorized["eks"].append(instance)
        elif is_ecs:
            categorized["ecs"].append(instance)
        else:
            categorized["standalone"].append(instance)

    return categorized


def generate_detailed_vpc_diagram(
    vpc_data: Dict[str, Any],
    ec2_instances: List[Dict],
    ecs_clusters: List[Dict],
    eks_clusters: List[Dict],
    rds_data: Dict[str, Any],
    elasticache_data: Dict[str, Any],
    load_balancers: Dict[str, Any],
    output_name: str,
    region: str,
    k8s_workloads: Dict[str, Any] = None,
    elasticbeanstalk_data: Dict[str, Any] = None,
    redshift_data: Dict[str, Any] = None
):
    """Generate detailed diagram for a single VPC."""
    vpc_id = vpc_data["vpc_id"]
    vpc_name = get_resource_name(vpc_data, "vpc_id", vpc_id)

    # Filter resources by VPC
    vpc_ec2 = [i for i in ec2_instances if i.get("vpc_id") == vpc_id]
    vpc_rds_instances = [r for r in rds_data.get("instances", []) if r.get("vpc_id") == vpc_id]
    vpc_rds_clusters = [r for r in rds_data.get("clusters", []) if r.get("vpc_id") == vpc_id]
    vpc_elasticache = elasticache_data.get("clusters", [])
    vpc_repl_groups = elasticache_data.get("replication_groups", [])

    # Elastic Beanstalk environments (filter by VPC name pattern)
    eb_data = elasticbeanstalk_data or {}
    vpc_beanstalk_envs = []
    for env in eb_data.get("environments", []):
        env_name = env.get("environment_name", "").lower()
        app_name = env.get("application_name", "").lower()
        if vpc_name.lower().replace("-", "") in env_name.replace("-", "") or \
           vpc_name.lower().replace("-", "") in app_name.replace("-", ""):
            vpc_beanstalk_envs.append(env)

    # Redshift clusters (filter by VPC)
    rs_data = redshift_data or {}
    vpc_redshift_clusters = [c for c in rs_data.get("clusters", []) if c.get("vpc_id") == vpc_id]
    vpc_redshift_serverless = [w for w in rs_data.get("serverless_workgroups", []) if w.get("vpc_id") == vpc_id]

    # Filter EKS clusters by VPC
    vpc_eks = [c for c in eks_clusters if c.get("vpc_id") == vpc_id]

    # Filter ECS by checking service subnets OR name pattern matching VPC
    vpc_subnet_ids = {s["subnet_id"] for s in vpc_data.get("subnets", [])}
    vpc_name_lower = vpc_name.lower().replace("-", "").replace("_", "")
    vpc_ecs = []
    for cluster in ecs_clusters:
        cluster_name_lower = cluster.get("cluster_name", "").lower().replace("-", "").replace("_", "")

        # Match by subnet or by name pattern
        name_match = (
            cluster_name_lower in vpc_name_lower or
            vpc_name_lower in cluster_name_lower or
            any(part in cluster_name_lower for part in vpc_name_lower.split() if len(part) > 3)
        )

        subnet_match = False
        for svc in cluster.get("services", []):
            if any(s in vpc_subnet_ids for s in svc.get("subnets", [])):
                subnet_match = True
                break

        if name_match or subnet_match:
            vpc_ecs.append(cluster)

    # Filter load balancers by VPC
    vpc_albs = [lb for lb in load_balancers.get("application_load_balancers", []) if lb.get("vpc_id") == vpc_id]
    vpc_nlbs = [lb for lb in load_balancers.get("network_load_balancers", []) if lb.get("vpc_id") == vpc_id]

    # Categorize EC2 instances
    ec2_categories = categorize_ec2_instances(vpc_ec2, vpc_ecs, vpc_eks)

    graph_attr = {
        "fontsize": "14",
        "fontname": "Sans-Serif",
        "bgcolor": "white",
        "pad": "1.0",
        "splines": "spline",
        "nodesep": "1.2",
        "ranksep": "1.5",
        "compound": "true",
        "concentrate": "false",
    }

    node_attr = {
        "fontsize": "11",
        "fontname": "Sans-Serif",
    }

    edge_attr = {
        "fontsize": "10",
        "fontname": "Sans-Serif",
    }

    # Cluster styling for vertical layout
    cluster_attr = {
        "fontsize": "13",
        "fontname": "Sans-Serif Bold",
        "style": "rounded",
        "margin": "20",
    }

    with Diagram(
        f"AWS Architecture - {vpc_name}",
        filename=output_name,
        show=False,
        direction="TB",
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        with Cluster(f"{region}", graph_attr={"margin": "30"}):
            with Cluster(f"{format_label(vpc_name, 25)} | {vpc_data['cidr_block']}", graph_attr={"margin": "25", "style": "rounded"}):

                # Internet Gateway & NAT
                igw_nodes = []
                nat_nodes = []

                with Cluster("Gateways", graph_attr={"margin": "15"}):
                    for igw in vpc_data.get("internet_gateways", []):
                        igw_name = format_label(igw.get("tags", {}).get("Name", "IGW"), 15)
                        igw_nodes.append(InternetGateway(igw_name))

                    for nat in vpc_data.get("nat_gateways", []):
                        if nat.get("state") == "available":
                            nat_name = format_label(nat.get("tags", {}).get("Name", "NAT"), 15)
                            nat_nodes.append(NATGateway(nat_name))

                # Load Balancers
                alb_nodes = []
                nlb_nodes = []
                if vpc_albs or vpc_nlbs:
                    with Cluster("Load Balancers", graph_attr={"margin": "15", "bgcolor": "#e3f2fd"}):
                        for alb in vpc_albs:
                            alb_name = format_label(alb.get("load_balancer_name", "ALB"), 20)
                            alb_nodes.append(ALB(alb_name))

                        for nlb in vpc_nlbs:
                            nlb_name = format_label(nlb.get("load_balancer_name", "NLB"), 20)
                            nlb_nodes.append(NLB(nlb_name))

                # Build mapping of EC2 instances to EKS node groups
                def get_eks_node_instances(ec2_list: List[Dict], cluster_name: str) -> Dict[str, List[Dict]]:
                    """Map EC2 instances to their EKS node groups."""
                    ng_instances = {}
                    for inst in ec2_list:
                        if inst.get("state") != "running":
                            continue
                        tags = inst.get("tags", {})
                        inst_cluster = tags.get("eks:cluster-name", "")
                        inst_ng = tags.get("eks:nodegroup-name", "")
                        if inst_cluster == cluster_name and inst_ng:
                            ng_instances.setdefault(inst_ng, []).append(inst)
                    return ng_instances

                # Get pods by node from k8s workloads
                def get_pods_for_cluster(cluster_name: str) -> Dict[str, List[Dict]]:
                    """Get pods grouped by node for a cluster."""
                    if not k8s_workloads:
                        return {}
                    cluster_data = k8s_workloads.get(cluster_name, {})
                    return cluster_data.get("pods_by_node", {})

                # EKS Clusters with Node Groups, EC2 Instances, and Pods
                eks_cluster_nodes = []
                eks_nodegroup_nodes = []
                for cluster in vpc_eks:
                    cluster_name = format_label(cluster.get("cluster_name", "EKS"), 20)
                    full_cluster_name = cluster.get("cluster_name", "")
                    version = cluster.get("version", "")

                    # Get EC2 instances mapped to node groups
                    ng_ec2_map = get_eks_node_instances(ec2_instances, full_cluster_name)

                    # Get pods by node
                    pods_by_node = get_pods_for_cluster(full_cluster_name)

                    with Cluster(f"EKS: {cluster_name} v{version}", graph_attr={"margin": "20", "bgcolor": "#fffaf3"}):
                        eks_node = EKS(cluster_name)
                        eks_cluster_nodes.append(eks_node)

                        # Node Groups with EC2 instances and Pods
                        for ng in cluster.get("node_groups", []):
                            ng_name = ng.get("nodegroup_name", "nodegroup")
                            ng_display = format_label(ng_name, 18)
                            instance_types = ng.get("instance_types", ["unknown"])
                            inst_type_short = instance_types[0].replace(".", "") if instance_types else "unknown"

                            # Get EC2 instances for this node group
                            ng_instances = ng_ec2_map.get(ng_name, [])

                            # Count total pods in this node group
                            total_pods = 0
                            for inst in ng_instances:
                                private_dns = f"ip-{inst.get('private_ip', '').replace('.', '-')}.{region}.compute.internal"
                                total_pods += len(pods_by_node.get(private_dns, []))

                            ng_label = f"{ng_display}\n{inst_type_short} | {len(ng_instances)}N | {total_pods}P"
                            with Cluster(ng_label, graph_attr={"margin": "15", "bgcolor": "#ffe0b2"}):
                                ng_header = EC2Instances(ng_display)
                                eks_nodegroup_nodes.append(ng_header)
                                eks_node - ng_header

                                # Show EC2 instances with their pods (limit to 5 nodes)
                                for inst in ng_instances[:5]:
                                    inst_name = format_label(inst.get("name", inst["instance_id"][:12]), 15)
                                    private_ip = inst.get("private_ip", "")
                                    private_dns = f"ip-{private_ip.replace('.', '-')}.{region}.compute.internal"

                                    # Get pods on this node
                                    node_pods = pods_by_node.get(private_dns, [])
                                    running_pods = [p for p in node_pods if p.get("status") == "Running"]
                                    # Filter out system pods
                                    app_pods = [p for p in running_pods if p.get("namespace") not in ["kube-system", "amazon-cloudwatch", "amazon-guardduty"]]

                                    node_label = f"{inst_name}\n{private_ip}\n{len(app_pods)} pods"
                                    with Cluster(node_label, graph_attr={"margin": "10", "bgcolor": "#ffcc80"}):
                                        EC2(inst.get('instance_type', ''))

                                        # Show pods (limit to 5 per node)
                                        for pod in app_pods[:5]:
                                            pod_name = format_label(pod.get("name", "pod"), 18)
                                            containers = pod.get("containers", [])
                                            image = format_label(containers[0].get("image", "") if containers else "", 15)
                                            Pod(f"{pod_name}\n{image}")

                                        # Show count of remaining pods
                                        if len(app_pods) > 5:
                                            Pod(f"+{len(app_pods) - 5} more")

                                # Show if more nodes exist
                                if len(ng_instances) > 5:
                                    EC2(f"+{len(ng_instances) - 5} nodes")

                        # Fargate Profiles
                        for fp in cluster.get("fargate_profiles", []):
                            fp_name = format_label(fp.get("fargate_profile_name", "fargate"), 18)
                            Fargate(fp_name)

                # ECS Clusters with Services
                ecs_cluster_nodes = []
                ecs_service_nodes = []
                for cluster in vpc_ecs:
                    cluster_name = format_label(cluster.get("cluster_name", "ECS"), 20)
                    services = cluster.get("services", [])

                    with Cluster(f"ECS: {cluster_name}", graph_attr={"margin": "20", "bgcolor": "#e8f5e9"}):
                        ecs_node = ECS(cluster_name)
                        ecs_cluster_nodes.append(ecs_node)

                        # Group services
                        running_services = [s for s in services if s.get("running_count", 0) > 0]
                        stopped_services = [s for s in services if s.get("running_count", 0) == 0]

                        if running_services:
                            with Cluster("Running", graph_attr={"margin": "15", "bgcolor": "#c8e6c9"}):
                                for svc in running_services[:8]:  # Limit to 8
                                    svc_name = format_label(svc.get("service_name", "service"), 18)
                                    task_name = format_label(extract_service_name(svc.get("task_definition")), 15)
                                    running = svc.get("running_count", 0)
                                    desired = svc.get("desired_count", 0)
                                    launch = svc.get("launch_type", "EC2")[:3]

                                    label = f"{svc_name}\n{running}/{desired} {launch}"
                                    svc_node = ElasticContainerServiceService(label)
                                    ecs_service_nodes.append(svc_node)
                                    ecs_node - svc_node

                                if len(running_services) > 8:
                                    ElasticContainerServiceService(f"+{len(running_services) - 8} more")

                        if stopped_services:
                            with Cluster("Stopped", graph_attr={"margin": "10", "bgcolor": "#ffcdd2"}):
                                for svc in stopped_services[:3]:
                                    svc_name = format_label(svc.get("service_name", "service"), 18)
                                    ElasticContainerServiceTask(f"{svc_name}")

                # Standalone EC2 Instances
                standalone_nodes = []
                if ec2_categories["standalone"]:
                    with Cluster(f"EC2 Standalone ({len(ec2_categories['standalone'])})", graph_attr={"margin": "15", "bgcolor": "#fce4ec"}):
                        for instance in ec2_categories["standalone"][:10]:  # Limit to 10
                            name = format_label(get_resource_name(instance, "instance_id"), 18)
                            inst_type = instance.get("instance_type", "")

                            label = f"{name}\n{inst_type}"
                            if "rabbitmq" in name.lower():
                                standalone_nodes.append(RabbitMQ(label))
                            elif "cassandra" in name.lower():
                                standalone_nodes.append(Cassandra(label))
                            else:
                                standalone_nodes.append(EC2(label))

                        if len(ec2_categories["standalone"]) > 10:
                            EC2(f"+{len(ec2_categories['standalone']) - 10} more")

                # ECS EC2 Instances (Container Instances)
                ecs_ec2_nodes = []
                if ec2_categories["ecs"]:
                    with Cluster(f"ECS Hosts ({len(ec2_categories['ecs'])})", graph_attr={"margin": "15", "bgcolor": "#e0f2f1"}):
                        by_type = {}
                        for inst in ec2_categories["ecs"]:
                            t = inst.get("instance_type", "unknown")
                            by_type.setdefault(t, []).append(inst)

                        for inst_type, instances in by_type.items():
                            label = f"{inst_type}\nx{len(instances)}"
                            ecs_ec2_nodes.append(EC2Instances(label))

                # EKS EC2 Instances (Worker Nodes) - already shown in node groups
                # Just show summary if there are extras
                eks_ec2_count = len(ec2_categories["eks"])

                # Elastic Beanstalk Environments
                beanstalk_nodes = []
                if vpc_beanstalk_envs:
                    with Cluster("Elastic Beanstalk", graph_attr={"margin": "15", "bgcolor": "#f3e5f5"}):
                        for env in vpc_beanstalk_envs:
                            env_name = format_label(env.get("environment_name", "EB Env"), 18)
                            app_name = format_label(env.get("application_name", ""), 15)
                            status = env.get("status", "")
                            health = env.get("health", "")
                            tier = env.get("tier_name", "Web")[:8]

                            resources = env.get("resources", {})
                            instance_count = len(resources.get("instances", []))

                            label = f"{env_name}\n{app_name}\n{tier} | {status}"
                            if instance_count:
                                label += f"\n{instance_count} inst"

                            beanstalk_nodes.append(ElasticBeanstalk(label))

                # Databases
                rds_nodes = []
                cache_nodes = []
                redshift_nodes = []
                if vpc_rds_instances or vpc_rds_clusters or vpc_elasticache or vpc_repl_groups or vpc_redshift_clusters or vpc_redshift_serverless:
                    with Cluster("Data Layer", graph_attr={"margin": "20", "bgcolor": "#e8eaf6"}):
                        # RDS
                        if vpc_rds_instances:
                            with Cluster("RDS", graph_attr={"margin": "15", "bgcolor": "#c5cae9"}):
                                for rds in vpc_rds_instances[:6]:  # Limit
                                    rds_name = format_label(rds.get("db_instance_identifier", "RDS"), 18)
                                    engine = rds.get("engine", "")[:12]
                                    inst_class = rds.get("db_instance_class", "").replace("db.", "")[:12]
                                    az_mode = "M-AZ" if rds.get("multi_az") else "S-AZ"

                                    label = f"{rds_name}\n{engine}\n{inst_class} | {az_mode}"

                                    if "aurora" in engine.lower():
                                        rds_nodes.append(Aurora(label))
                                    else:
                                        rds_nodes.append(RDS(label))

                                if len(vpc_rds_instances) > 6:
                                    RDS(f"+{len(vpc_rds_instances) - 6} more")

                        # Aurora Clusters
                        if vpc_rds_clusters:
                            with Cluster("Aurora", graph_attr={"margin": "15", "bgcolor": "#b39ddb"}):
                                for cluster in vpc_rds_clusters:
                                    cluster_name = format_label(cluster.get("db_cluster_identifier", "Aurora"), 18)
                                    engine = cluster.get("engine", "aurora")[:10]
                                    members = len(cluster.get("cluster_members", []))

                                    label = f"{cluster_name}\n{engine}\n{members} inst"
                                    rds_nodes.append(Aurora(label))

                        # ElastiCache
                        if vpc_elasticache or vpc_repl_groups:
                            with Cluster("ElastiCache", graph_attr={"margin": "15", "bgcolor": "#ffccbc"}):
                                for cache in vpc_elasticache:
                                    cache_name = format_label(cache.get("cache_cluster_id", "Cache"), 18)
                                    engine = cache.get("engine", "redis")[:8]
                                    node_type = cache.get("cache_node_type", "").replace("cache.", "")[:10]

                                    label = f"{cache_name}\n{engine} | {node_type}"
                                    cache_nodes.append(ElastiCache(label))

                                for rg in vpc_repl_groups:
                                    rg_name = format_label(rg.get("replication_group_id", "Redis"), 18)
                                    num_nodes = rg.get("num_cache_clusters", 0)
                                    mode = "Clust" if rg.get("cluster_enabled") else "Repl"

                                    label = f"{rg_name}\nRedis {mode}\n{num_nodes} nodes"
                                    cache_nodes.append(ElastiCache(label))

                        # Redshift
                        if vpc_redshift_clusters or vpc_redshift_serverless:
                            with Cluster("Redshift", graph_attr={"margin": "15", "bgcolor": "#b2dfdb"}):
                                for cluster in vpc_redshift_clusters:
                                    cluster_name = format_label(cluster.get("cluster_identifier", "Redshift"), 18)
                                    node_type = cluster.get("node_type", "")[:10]
                                    num_nodes = cluster.get("number_of_nodes", 1)
                                    status = cluster.get("cluster_status", "")[:8]

                                    label = f"{cluster_name}\n{node_type}\n{num_nodes}N | {status}"
                                    redshift_nodes.append(Redshift(label))

                                for wg in vpc_redshift_serverless:
                                    wg_name = format_label(wg.get("workgroup_name", "Serverless"), 18)
                                    base_cap = wg.get("base_capacity", 0)

                                    label = f"{wg_name}\nServerless\n{base_cap} RPU"
                                    redshift_nodes.append(Redshift(label))

                # Draw connections
                # IGW -> LBs
                for igw in igw_nodes:
                    for alb in alb_nodes[:5]:
                        igw >> Edge(color="darkgreen", style="bold") >> alb
                    for nlb in nlb_nodes[:3]:
                        igw >> Edge(color="darkgreen", style="bold") >> nlb

                # LBs -> ECS Services
                for alb in alb_nodes[:3]:
                    for svc in ecs_service_nodes[:3]:
                        alb >> Edge(color="blue") >> svc
                    for eks in eks_cluster_nodes:
                        alb >> Edge(color="blue") >> eks

                # ECS -> Data
                for ecs in ecs_cluster_nodes:
                    for rds in rds_nodes[:2]:
                        ecs >> Edge(color="purple", style="dashed") >> rds
                    for cache in cache_nodes[:2]:
                        ecs >> Edge(color="red", style="dashed") >> cache

                # EKS -> Data
                for eks in eks_cluster_nodes:
                    for rds in rds_nodes[:2]:
                        eks >> Edge(color="purple", style="dashed") >> rds
                    for cache in cache_nodes[:2]:
                        eks >> Edge(color="red", style="dashed") >> cache
                    for rs in redshift_nodes[:1]:
                        eks >> Edge(color="brown", style="dashed") >> rs

                # LBs -> Beanstalk
                for alb in alb_nodes[:2]:
                    for eb in beanstalk_nodes[:2]:
                        alb >> Edge(color="green") >> eb

                # Beanstalk -> Data
                for eb in beanstalk_nodes:
                    for rds in rds_nodes[:1]:
                        eb >> Edge(color="purple", style="dashed") >> rds
                    for cache in cache_nodes[:1]:
                        eb >> Edge(color="red", style="dashed") >> cache


def main():
    parser = argparse.ArgumentParser(description="Generate detailed AWS architecture diagrams")
    parser.add_argument(
        "--input",
        default="output/inventory.json",
        help="Path to inventory JSON file"
    )
    parser.add_argument(
        "--output",
        default="output/architecture_detailed",
        help="Output file path (without extension)"
    )
    parser.add_argument(
        "--vpc",
        help="Generate diagram for specific VPC ID"
    )
    parser.add_argument(
        "--k8s-workloads",
        default="output/k8s_workloads.json",
        help="Path to K8s workloads JSON file"
    )
    args = parser.parse_args()

    # Load inventory
    print(f"Loading inventory from {args.input}...")
    inventory = load_inventory(args.input)

    # Load K8s workloads if available
    k8s_workloads = load_k8s_workloads(args.k8s_workloads)
    if k8s_workloads:
        print(f"Loaded K8s workloads for {len(k8s_workloads)} clusters")

    # Create output directory
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate per-VPC diagrams
    diagram_count = 0
    for region_name, region_data in inventory.get("regions", {}).items():
        if "error" in region_data:
            if not args.vpc:
                print(f"Skipping {region_name} (error in data)")
            continue

        vpcs = region_data.get("vpcs", [])

        # Filter to specific VPC if provided
        if args.vpc:
            vpcs = [v for v in vpcs if v["vpc_id"] == args.vpc]
            if not vpcs:
                continue

        ec2_instances = region_data.get("ec2_instances", [])
        ecs_clusters = region_data.get("ecs_clusters", [])
        eks_clusters = region_data.get("eks_clusters", [])
        rds_data = region_data.get("rds", {})
        elasticache_data = region_data.get("elasticache", {})
        load_balancers = region_data.get("load_balancers", {})
        elasticbeanstalk_data = region_data.get("elasticbeanstalk", {})
        redshift_data = region_data.get("redshift", {})

        for vpc in vpcs:
            vpc_id = vpc["vpc_id"]

            # Skip default VPCs with no resources (only when generating all)
            if not args.vpc and vpc.get("is_default"):
                continue

            vpc_name = get_resource_name(vpc, "vpc_id")
            safe_name = vpc_name.replace(" ", "_").replace("/", "_").replace("-", "_")
            output_file = f"{args.output}_{region_name}_{safe_name}"

            print(f"Generating diagram for VPC: {vpc_name} ({vpc_id})...")

            generate_detailed_vpc_diagram(
                vpc,
                ec2_instances,
                ecs_clusters,
                eks_clusters,
                rds_data,
                elasticache_data,
                load_balancers,
                output_file,
                region_name,
                k8s_workloads,
                elasticbeanstalk_data,
                redshift_data
            )
            print(f"  Created: {output_file}.png")
            diagram_count += 1

    if diagram_count == 0 and args.vpc:
        print(f"Error: VPC {args.vpc} not found in inventory")
    else:
        print(f"\nDiagram generation complete! Generated {diagram_count} diagram(s).")


if __name__ == "__main__":
    main()
