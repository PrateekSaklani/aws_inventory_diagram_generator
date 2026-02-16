#!/usr/bin/env python3
"""
AWS Architecture Diagram Generator - Draw.io Output (Detailed)

Generates draw.io compatible XML files with full detail matching PNG output.
"""

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List


def load_inventory(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r") as f:
        return json.load(f)


def load_k8s_workloads(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_resource_name(resource: Dict, default_key: str, fallback: str = "unnamed") -> str:
    name = resource.get("name") or resource.get("tags", {}).get("Name")
    if name:
        return name[:35]
    return resource.get(default_key, fallback)[:35]


def format_label(name: str, max_len: int = 20) -> str:
    if len(name) <= max_len:
        return name
    return name[:max_len-2] + ".."


def extract_service_name(task_def_arn: str) -> str:
    if not task_def_arn:
        return "unknown"
    match = re.search(r'task-definition/([^:]+)', task_def_arn)
    if match:
        return match.group(1)
    return task_def_arn.split('/')[-1].split(':')[0]


class DrawIOGenerator:
    """Generates draw.io XML diagrams."""

    AWS_STYLES = {
        "vpc": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;strokeColor=#232F3E;fillColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpc;",
        "igw": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_gateway;",
        "nat": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.nat_gateway;",
        "alb": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.application_load_balancer;",
        "nlb": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.network_load_balancer;",
        "ec2": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;",
        "ec2_instances": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2_instances;",
        "ecs": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs;",
        "ecs_service": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs_service;",
        "ecs_task": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs_task;",
        "eks": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;",
        "fargate": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.fargate;",
        "rds": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;",
        "aurora": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.aurora;",
        "elasticache": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticache;",
        "redshift": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.redshift;",
        "beanstalk": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_beanstalk;",
        "pod": "sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#326CE5;strokeColor=#ffffff;points=[[0.5,0,0],[0.5,1,0]];verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon2;kubernetesLabel=1;prIcon=pod;",
        "rabbitmq": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#FF6600;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.mq;",
        "cassandra": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.keyspaces;",
        "cloudfront": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudfront;",
        "s3": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#60A337;gradientDirection=north;fillColor=#277116;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.s3;",
        "route53": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.route_53;",
        "waf": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F54749;gradientDirection=north;fillColor=#C7131F;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.waf;",
        "users": "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#232F3D;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.users;",
    }

    def __init__(self):
        self.cell_id = 2
        self.cells = []
        self.edges = []

    def _next_id(self) -> str:
        self.cell_id += 1
        return str(self.cell_id)

    def add_group(self, label: str, x: int, y: int, width: int, height: int,
                  parent: str = "1", style: str = None, bgcolor: str = "#E6F2FF") -> str:
        cell_id = self._next_id()
        default_style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={bgcolor};strokeColor=#147eba;dashed=0;verticalAlign=top;fontStyle=1;fontSize=11;"
        self.cells.append({
            "id": cell_id,
            "value": label,
            "style": style or default_style,
            "vertex": "1",
            "parent": parent,
            "geometry": {"x": x, "y": y, "width": width, "height": height}
        })
        return cell_id

    def add_node(self, label: str, node_type: str, x: int, y: int,
                 parent: str = "1", width: int = 48, height: int = 48) -> str:
        cell_id = self._next_id()
        style = self.AWS_STYLES.get(node_type, self.AWS_STYLES["ec2"])
        self.cells.append({
            "id": cell_id,
            "value": label,
            "style": style,
            "vertex": "1",
            "parent": parent,
            "geometry": {"x": x, "y": y, "width": width, "height": height}
        })
        return cell_id

    def add_edge(self, source: str, target: str, label: str = "", style: str = None) -> str:
        cell_id = self._next_id()
        default_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;"
        self.edges.append({
            "id": cell_id,
            "value": label,
            "style": style or default_style,
            "edge": "1",
            "parent": "1",
            "source": source,
            "target": target
        })
        return cell_id

    def generate_xml(self, title: str) -> str:
        mxfile = ET.Element("mxfile", {
            "host": "app.diagrams.net",
            "modified": "2024-01-01T00:00:00.000Z",
            "agent": "AWS Diagram Generator",
            "version": "21.0.0",
            "type": "device"
        })

        diagram = ET.SubElement(mxfile, "diagram", {"id": "diagram-1", "name": title})

        mxGraphModel = ET.SubElement(diagram, "mxGraphModel", {
            "dx": "1400", "dy": "900", "grid": "1", "gridSize": "10",
            "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
            "fold": "1", "page": "1", "pageScale": "1",
            "pageWidth": "2400", "pageHeight": "1800", "math": "0", "shadow": "0"
        })

        root = ET.SubElement(mxGraphModel, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

        for cell in self.cells:
            cell_elem = ET.SubElement(root, "mxCell", {
                "id": cell["id"], "value": cell["value"], "style": cell["style"],
                "vertex": cell["vertex"], "parent": cell["parent"]
            })
            geom = cell["geometry"]
            ET.SubElement(cell_elem, "mxGeometry", {
                "x": str(geom["x"]), "y": str(geom["y"]),
                "width": str(geom["width"]), "height": str(geom["height"]), "as": "geometry"
            })

        for edge in self.edges:
            edge_elem = ET.SubElement(root, "mxCell", {
                "id": edge["id"], "value": edge["value"], "style": edge["style"],
                "edge": edge["edge"], "parent": edge["parent"],
                "source": edge["source"], "target": edge["target"]
            })
            ET.SubElement(edge_elem, "mxGeometry", {"relative": "1", "as": "geometry"})

        return ET.tostring(mxfile, encoding="unicode", xml_declaration=True)


def categorize_ec2_instances(ec2_instances: List[Dict], ecs_clusters: List[Dict], eks_clusters: List[Dict]) -> Dict[str, List[Dict]]:
    eks_patterns = set()
    for cluster in eks_clusters:
        eks_patterns.add(cluster.get("cluster_name", "").lower())
        for ng in cluster.get("node_groups", []):
            eks_patterns.add(ng.get("nodegroup_name", "").lower())

    ecs_patterns = set()
    for cluster in ecs_clusters:
        ecs_patterns.add(cluster.get("cluster_name", "").lower())

    categorized = {"standalone": [], "ecs": [], "eks": []}

    for instance in ec2_instances:
        if instance.get("state") != "running":
            continue
        tags = instance.get("tags", {})
        name = instance.get("name", "").lower()
        all_tags = " ".join(f"{k}={v}" for k, v in tags.items()).lower()

        is_eks = "kubernetes.io" in all_tags or "eks" in all_tags or "karpenter" in all_tags or any(p in name or p in all_tags for p in eks_patterns if p)
        is_ecs = "ecs" in all_tags or "ecs:cluster" in all_tags or any(p in name for p in ecs_patterns if p)

        if is_eks:
            categorized["eks"].append(instance)
        elif is_ecs:
            categorized["ecs"].append(instance)
        else:
            categorized["standalone"].append(instance)

    return categorized


def get_eks_node_instances(ec2_list: List[Dict], cluster_name: str) -> Dict[str, List[Dict]]:
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


def get_pods_for_cluster(k8s_workloads: Dict, cluster_name: str) -> Dict[str, List[Dict]]:
    if not k8s_workloads:
        return {}
    cluster_data = k8s_workloads.get(cluster_name, {})
    return cluster_data.get("pods_by_node", {})


def generate_drawio_diagram(
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
    redshift_data: Dict[str, Any] = None,
    cloudfront_data: Dict[str, Any] = None
):
    vpc_id = vpc_data["vpc_id"]
    vpc_name = get_resource_name(vpc_data, "vpc_id", vpc_id)

    # Filter resources by VPC
    vpc_ec2 = [i for i in ec2_instances if i.get("vpc_id") == vpc_id]
    vpc_rds_instances = [r for r in rds_data.get("instances", []) if r.get("vpc_id") == vpc_id]
    vpc_rds_clusters = [r for r in rds_data.get("clusters", []) if r.get("vpc_id") == vpc_id]
    vpc_elasticache = elasticache_data.get("clusters", [])
    vpc_repl_groups = elasticache_data.get("replication_groups", [])

    eb_data = elasticbeanstalk_data or {}
    vpc_beanstalk_envs = []
    for env in eb_data.get("environments", []):
        env_name = env.get("environment_name", "").lower()
        app_name = env.get("application_name", "").lower()
        if vpc_name.lower().replace("-", "") in env_name.replace("-", "") or vpc_name.lower().replace("-", "") in app_name.replace("-", ""):
            vpc_beanstalk_envs.append(env)

    rs_data = redshift_data or {}
    vpc_redshift_clusters = [c for c in rs_data.get("clusters", []) if c.get("vpc_id") == vpc_id]
    vpc_redshift_serverless = [w for w in rs_data.get("serverless_workgroups", []) if w.get("vpc_id") == vpc_id]

    vpc_eks = [c for c in eks_clusters if c.get("vpc_id") == vpc_id]

    vpc_subnet_ids = {s["subnet_id"] for s in vpc_data.get("subnets", [])}
    vpc_name_lower = vpc_name.lower().replace("-", "").replace("_", "").replace(" ", "")
    vpc_ecs = []
    for cluster in ecs_clusters:
        cluster_name_lower = cluster.get("cluster_name", "").lower().replace("-", "").replace("_", "").replace(" ", "")
        name_match = cluster_name_lower in vpc_name_lower or vpc_name_lower in cluster_name_lower
        subnet_match = any(any(s in vpc_subnet_ids for s in svc.get("subnets", [])) for svc in cluster.get("services", []))
        if name_match or subnet_match:
            vpc_ecs.append(cluster)

    vpc_albs = [lb for lb in load_balancers.get("application_load_balancers", []) if lb.get("vpc_id") == vpc_id]
    vpc_nlbs = [lb for lb in load_balancers.get("network_load_balancers", []) if lb.get("vpc_id") == vpc_id]

    ec2_categories = categorize_ec2_instances(vpc_ec2, vpc_ecs, vpc_eks)

    # Filter CloudFront distributions that might be related to this VPC's load balancers
    cf_data = cloudfront_data or {}
    vpc_cloudfront = []
    vpc_lb_dns = set()
    for alb in vpc_albs:
        vpc_lb_dns.add(alb.get("dns_name", "").lower())
    for nlb in vpc_nlbs:
        vpc_lb_dns.add(nlb.get("dns_name", "").lower())

    for dist in cf_data.get("distributions", []):
        for origin in dist.get("origins", []):
            origin_domain = origin.get("domain_name", "").lower()
            # Check if origin points to our LBs or has matching VPC name pattern
            if any(lb_dns in origin_domain for lb_dns in vpc_lb_dns if lb_dns):
                vpc_cloudfront.append(dist)
                break
            if vpc_name.lower().replace("-", "").replace("_", "") in origin_domain.replace("-", "").replace("_", ""):
                vpc_cloudfront.append(dist)
                break

    gen = DrawIOGenerator()

    # Layout
    x_start, y_start = 20, 20
    current_y = y_start
    node_refs = {}

    # Row 0: CloudFront (Edge/CDN - outside VPC)
    cf_refs = []
    if vpc_cloudfront or cf_data.get("distributions"):
        # Show related CloudFront or all if no specific match
        dists_to_show = vpc_cloudfront if vpc_cloudfront else cf_data.get("distributions", [])[:5]
        if dists_to_show:
            cf_width = len(dists_to_show) * 120 + 60
            cf_group = gen.add_group("Edge / CDN (CloudFront)", x_start, current_y, cf_width, 110, bgcolor="#F3E5F5")

            # Add users icon
            gen.add_node("Users", "users", 15, 30, cf_group)

            cf_x = 80
            for dist in dists_to_show[:6]:
                dist_id = dist.get("id", "")[:12]
                domain = format_label(dist.get("domain_name", ""), 18)
                aliases = dist.get("aliases", [])
                alias_str = format_label(aliases[0] if aliases else "", 15)
                status = "ON" if dist.get("enabled") else "OFF"

                label = f"{dist_id}\\n{alias_str}\\n{status}"
                ref = gen.add_node(label, "cloudfront", cf_x, 25, cf_group)
                cf_refs.append(ref)
                cf_x += 110

            node_refs["cloudfront"] = cf_refs
            current_y += 130

    # VPC container
    vpc_y_start = current_y
    vpc_group = gen.add_group(f"{vpc_name} | {vpc_data['cidr_block']}", x_start, vpc_y_start, 2200, 1600, bgcolor="#E6F2FF")
    current_y = 50  # Reset for inside VPC

    # Row 1: Gateways
    gw_group = gen.add_group("Gateways", 20, current_y, 300, 100, vpc_group, bgcolor="#F3E5F5")
    gw_x = 20
    for igw in vpc_data.get("internet_gateways", []):
        igw_name = format_label(igw.get("tags", {}).get("Name", "IGW"), 15)
        node_refs["igw"] = gen.add_node(igw_name, "igw", gw_x, 25, gw_group)
        gw_x += 70

    for nat in vpc_data.get("nat_gateways", []):
        if nat.get("state") == "available":
            nat_name = format_label(nat.get("tags", {}).get("Name", "NAT"), 15)
            gen.add_node(nat_name, "nat", gw_x, 25, gw_group)
            gw_x += 70

    current_y = 160

    # Row 2: Load Balancers
    if vpc_albs or vpc_nlbs:
        lb_width = max(400, (len(vpc_albs) + len(vpc_nlbs)) * 80 + 40)
        lb_group = gen.add_group("Load Balancers", 20, current_y, lb_width, 100, vpc_group, bgcolor="#FFF3E0")
        lb_x = 20
        alb_refs = []
        for alb in vpc_albs:
            alb_name = format_label(alb.get("load_balancer_name", "ALB"), 18)
            ref = gen.add_node(alb_name, "alb", lb_x, 25, lb_group)
            alb_refs.append(ref)
            lb_x += 80
        for nlb in vpc_nlbs:
            nlb_name = format_label(nlb.get("load_balancer_name", "NLB"), 18)
            gen.add_node(nlb_name, "nlb", lb_x, 25, lb_group)
            lb_x += 80
        node_refs["albs"] = alb_refs
        current_y += 120

    # Row 3: EKS Clusters with Node Groups and Pods
    eks_start_y = current_y
    eks_refs = []
    eks_x = 20

    for cluster in vpc_eks:
        cluster_name = cluster.get("cluster_name", "EKS")
        version = cluster.get("version", "")
        node_groups = cluster.get("node_groups", [])
        fargate_profiles = cluster.get("fargate_profiles", [])

        ng_ec2_map = get_eks_node_instances(ec2_instances, cluster_name)
        pods_by_node = get_pods_for_cluster(k8s_workloads, cluster_name)

        # Calculate EKS cluster size
        eks_height = 150
        ng_width = 0
        for ng in node_groups:
            ng_instances = ng_ec2_map.get(ng.get("nodegroup_name", ""), [])
            ng_width += max(180, min(len(ng_instances), 5) * 100 + 100)
        eks_width = max(400, ng_width + 150)

        eks_group = gen.add_group(f"EKS: {format_label(cluster_name, 25)} v{version}", eks_x, current_y, eks_width, eks_height + len(node_groups) * 200, vpc_group, bgcolor="#FFFAF3")

        eks_ref = gen.add_node(format_label(cluster_name, 15), "eks", 20, 35, eks_group)
        eks_refs.append(eks_ref)

        ng_y = 100
        ng_x = 20

        for ng in node_groups:
            ng_name = ng.get("nodegroup_name", "nodegroup")
            instance_types = ng.get("instance_types") or ["unknown"]
            ng_instances = ng_ec2_map.get(ng_name, [])

            # Count pods
            total_pods = 0
            for inst in ng_instances:
                private_dns = f"ip-{inst.get('private_ip', '').replace('.', '-')}.{region}.compute.internal"
                total_pods += len(pods_by_node.get(private_dns, []))

            ng_display_width = max(180, min(len(ng_instances), 5) * 100 + 80)
            ng_label = f"{format_label(ng_name, 18)}\\n{instance_types[0]} | {len(ng_instances)}N | {total_pods}P"

            ng_group = gen.add_group(ng_label, ng_x, ng_y, ng_display_width, 180, eks_group, bgcolor="#FFE0B2")
            gen.add_node(format_label(ng_name, 12), "ec2_instances", 10, 30, ng_group, 40, 40)

            # Show EC2 instances with pods
            inst_x = 60
            for inst in ng_instances[:5]:
                inst_name = format_label(inst.get("name", inst["instance_id"][:10]), 12)
                private_ip = inst.get("private_ip", "")
                private_dns = f"ip-{private_ip.replace('.', '-')}.{region}.compute.internal"

                node_pods = pods_by_node.get(private_dns, [])
                running_pods = [p for p in node_pods if p.get("status") == "Running"]
                app_pods = [p for p in running_pods if p.get("namespace") not in ["kube-system", "amazon-cloudwatch", "amazon-guardduty"]]

                node_label = f"{inst_name}\\n{private_ip}\\n{len(app_pods)} pods"
                node_group = gen.add_group(node_label, inst_x, 30, 90, 140, ng_group, bgcolor="#FFCC80")
                gen.add_node(inst.get('instance_type', ''), "ec2", 20, 30, node_group, 40, 40)

                # Show pods
                pod_y = 80
                for pod in app_pods[:3]:
                    pod_name = format_label(pod.get("name", "pod"), 10)
                    gen.add_node(pod_name, "pod", 25, pod_y, node_group, 35, 35)
                    pod_y += 20

                inst_x += 95

            if len(ng_instances) > 5:
                gen.add_node(f"+{len(ng_instances) - 5} more", "ec2", inst_x, 60, ng_group, 40, 40)

            ng_x += ng_display_width + 20

        # Fargate profiles
        for fp in fargate_profiles:
            fp_name = format_label(fp.get("fargate_profile_name", "fargate"), 15)
            gen.add_node(fp_name, "fargate", ng_x, ng_y + 50, eks_group)
            ng_x += 70

        eks_x += eks_width + 30

    node_refs["eks"] = eks_refs
    current_y += 450

    # Row 4: ECS Clusters with Services
    ecs_refs = []
    ecs_svc_refs = []
    ecs_x = 20

    for cluster in vpc_ecs:
        cluster_name = cluster.get("cluster_name", "ECS")
        services = cluster.get("services", [])
        running_services = [s for s in services if s.get("running_count", 0) > 0]
        stopped_services = [s for s in services if s.get("running_count", 0) == 0]

        ecs_width = max(350, len(running_services[:8]) * 70 + 150)
        ecs_height = 200 if stopped_services else 150

        ecs_group = gen.add_group(f"ECS: {format_label(cluster_name, 25)}", ecs_x, current_y, ecs_width, ecs_height, vpc_group, bgcolor="#E8F5E9")
        ecs_ref = gen.add_node(format_label(cluster_name, 15), "ecs", 20, 35, ecs_group)
        ecs_refs.append(ecs_ref)

        if running_services:
            running_group = gen.add_group("Running", 100, 25, len(running_services[:8]) * 70 + 40, 80, ecs_group, bgcolor="#C8E6C9")
            svc_x = 15
            for svc in running_services[:8]:
                svc_name = format_label(svc.get("service_name", "service"), 12)
                running = svc.get("running_count", 0)
                desired = svc.get("desired_count", 0)
                launch = svc.get("launch_type", "EC2")[:3]
                label = f"{svc_name}\\n{running}/{desired} {launch}"
                svc_ref = gen.add_node(label, "ecs_service", svc_x, 20, running_group, 50, 50)
                ecs_svc_refs.append(svc_ref)
                svc_x += 65

            if len(running_services) > 8:
                gen.add_node(f"+{len(running_services) - 8}", "ecs_service", svc_x, 20, running_group, 40, 40)

        if stopped_services:
            stopped_group = gen.add_group("Stopped", 100, 110, len(stopped_services[:3]) * 60 + 30, 70, ecs_group, bgcolor="#FFCDD2")
            svc_x = 10
            for svc in stopped_services[:3]:
                svc_name = format_label(svc.get("service_name", "service"), 10)
                gen.add_node(svc_name, "ecs_task", svc_x, 15, stopped_group, 40, 40)
                svc_x += 55

        ecs_x += ecs_width + 30

    node_refs["ecs"] = ecs_refs
    node_refs["ecs_svcs"] = ecs_svc_refs
    current_y += 220

    # Row 5: Standalone EC2 + ECS Hosts
    if ec2_categories["standalone"]:
        standalone_width = min(len(ec2_categories["standalone"][:10]) * 75 + 40, 800)
        standalone_group = gen.add_group(f"EC2 Standalone ({len(ec2_categories['standalone'])})", 20, current_y, standalone_width, 100, vpc_group, bgcolor="#FCE4EC")
        ec2_x = 15
        for instance in ec2_categories["standalone"][:10]:
            name = format_label(get_resource_name(instance, "instance_id"), 12)
            inst_type = instance.get("instance_type", "")[:10]
            label = f"{name}\\n{inst_type}"

            node_type = "ec2"
            if "rabbitmq" in name.lower():
                node_type = "rabbitmq"
            elif "cassandra" in name.lower():
                node_type = "cassandra"

            gen.add_node(label, node_type, ec2_x, 25, standalone_group)
            ec2_x += 70

        if len(ec2_categories["standalone"]) > 10:
            gen.add_node(f"+{len(ec2_categories['standalone']) - 10}", "ec2", ec2_x, 25, standalone_group, 40, 40)

    # ECS Hosts
    if ec2_categories["ecs"]:
        by_type = {}
        for inst in ec2_categories["ecs"]:
            t = inst.get("instance_type", "unknown")
            by_type.setdefault(t, []).append(inst)

        ecs_hosts_width = len(by_type) * 80 + 40
        ecs_hosts_x = 20 + (standalone_width + 30 if ec2_categories["standalone"] else 0)
        ecs_hosts_group = gen.add_group(f"ECS Hosts ({len(ec2_categories['ecs'])})", ecs_hosts_x, current_y, ecs_hosts_width, 100, vpc_group, bgcolor="#E0F2F1")

        host_x = 15
        for inst_type, instances in by_type.items():
            label = f"{inst_type}\\nx{len(instances)}"
            gen.add_node(label, "ec2_instances", host_x, 25, ecs_hosts_group)
            host_x += 75

    current_y += 120

    # Row 6: Elastic Beanstalk
    if vpc_beanstalk_envs:
        eb_width = len(vpc_beanstalk_envs) * 100 + 40
        eb_group = gen.add_group("Elastic Beanstalk", 20, current_y, eb_width, 110, vpc_group, bgcolor="#F3E5F5")
        eb_x = 15
        eb_refs = []
        for env in vpc_beanstalk_envs:
            env_name = format_label(env.get("environment_name", "EB"), 15)
            app_name = format_label(env.get("application_name", ""), 12)
            status = env.get("status", "")
            tier = env.get("tier_name", "Web")[:6]
            resources = env.get("resources", {})
            inst_count = len(resources.get("instances", []))

            label = f"{env_name}\\n{app_name}\\n{tier}|{status}"
            if inst_count:
                label += f"\\n{inst_count} inst"

            ref = gen.add_node(label, "beanstalk", eb_x, 25, eb_group)
            eb_refs.append(ref)
            eb_x += 90

        node_refs["beanstalk"] = eb_refs
        current_y += 130

    # Row 7: Data Layer
    db_y = current_y
    db_x = 20
    rds_refs = []
    cache_refs = []

    # RDS / Aurora
    if vpc_rds_instances or vpc_rds_clusters:
        rds_count = len(vpc_rds_instances) + len(vpc_rds_clusters)
        rds_width = min(rds_count * 85 + 40, 600)
        rds_group = gen.add_group("RDS / Aurora", db_x, db_y, rds_width, 110, vpc_group, bgcolor="#C5CAE9")

        rds_x = 15
        for rds in vpc_rds_instances[:6]:
            rds_name = format_label(rds.get("db_instance_identifier", "RDS"), 12)
            engine = rds.get("engine", "")[:10]
            inst_class = rds.get("db_instance_class", "").replace("db.", "")[:10]
            az_mode = "M-AZ" if rds.get("multi_az") else "S-AZ"
            label = f"{rds_name}\\n{engine}\\n{inst_class}|{az_mode}"

            node_type = "aurora" if "aurora" in engine.lower() else "rds"
            ref = gen.add_node(label, node_type, rds_x, 25, rds_group)
            rds_refs.append(ref)
            rds_x += 80

        for cluster in vpc_rds_clusters[:3]:
            cluster_name = format_label(cluster.get("db_cluster_identifier", "Aurora"), 12)
            engine = cluster.get("engine", "aurora")[:8]
            members = len(cluster.get("cluster_members", []))
            label = f"{cluster_name}\\n{engine}\\n{members} inst"
            ref = gen.add_node(label, "aurora", rds_x, 25, rds_group)
            rds_refs.append(ref)
            rds_x += 80

        db_x += rds_width + 20

    node_refs["rds"] = rds_refs

    # ElastiCache
    if vpc_elasticache or vpc_repl_groups:
        cache_count = len(vpc_elasticache) + len(vpc_repl_groups)
        cache_width = min(cache_count * 85 + 40, 400)
        cache_group = gen.add_group("ElastiCache", db_x, db_y, cache_width, 110, vpc_group, bgcolor="#FFCCBC")

        cache_x = 15
        for cache in vpc_elasticache[:4]:
            cache_name = format_label(cache.get("cache_cluster_id", "Cache"), 12)
            engine = cache.get("engine", "redis")[:6]
            node_type_ec = cache.get("cache_node_type", "").replace("cache.", "")[:8]
            label = f"{cache_name}\\n{engine}|{node_type_ec}"
            ref = gen.add_node(label, "elasticache", cache_x, 25, cache_group)
            cache_refs.append(ref)
            cache_x += 80

        for rg in vpc_repl_groups[:3]:
            rg_name = format_label(rg.get("replication_group_id", "Redis"), 12)
            num_nodes = rg.get("num_cache_clusters", 0)
            mode = "Clust" if rg.get("cluster_enabled") else "Repl"
            label = f"{rg_name}\\nRedis {mode}\\n{num_nodes} nodes"
            ref = gen.add_node(label, "elasticache", cache_x, 25, cache_group)
            cache_refs.append(ref)
            cache_x += 80

        db_x += cache_width + 20

    node_refs["cache"] = cache_refs

    # Redshift
    if vpc_redshift_clusters or vpc_redshift_serverless:
        rs_count = len(vpc_redshift_clusters) + len(vpc_redshift_serverless)
        rs_width = rs_count * 85 + 40
        rs_group = gen.add_group("Redshift", db_x, db_y, rs_width, 110, vpc_group, bgcolor="#B2DFDB")

        rs_x = 15
        for cluster in vpc_redshift_clusters:
            cluster_name = format_label(cluster.get("cluster_identifier", "RS"), 12)
            node_type_rs = cluster.get("node_type", "")[:8]
            num_nodes = cluster.get("number_of_nodes", 1)
            label = f"{cluster_name}\\n{node_type_rs}\\n{num_nodes}N"
            gen.add_node(label, "redshift", rs_x, 25, rs_group)
            rs_x += 80

        for wg in vpc_redshift_serverless:
            wg_name = format_label(wg.get("workgroup_name", "Serverless"), 12)
            base_cap = wg.get("base_capacity", 0)
            label = f"{wg_name}\\nServerless\\n{base_cap} RPU"
            gen.add_node(label, "redshift", rs_x, 25, rs_group)
            rs_x += 80

    # Add connections
    # CloudFront -> ALBs (if CloudFront exists)
    for cf_ref in node_refs.get("cloudfront", [])[:3]:
        for alb_ref in node_refs.get("albs", [])[:3]:
            gen.add_edge(cf_ref, alb_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#5A30B5;strokeWidth=2;")

    # IGW -> ALBs
    if "igw" in node_refs and "albs" in node_refs:
        for alb_ref in node_refs["albs"][:5]:
            gen.add_edge(node_refs["igw"], alb_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2E7D32;strokeWidth=2;")

    # ALBs -> EKS/ECS
    for alb_ref in node_refs.get("albs", [])[:3]:
        for eks_ref in node_refs.get("eks", []):
            gen.add_edge(alb_ref, eks_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#1976D2;strokeWidth=1;")
        for svc_ref in node_refs.get("ecs_svcs", [])[:3]:
            gen.add_edge(alb_ref, svc_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#1976D2;strokeWidth=1;")

    # EKS -> Data
    for eks_ref in node_refs.get("eks", []):
        for rds_ref in node_refs.get("rds", [])[:2]:
            gen.add_edge(eks_ref, rds_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7B1FA2;strokeWidth=1;dashed=1;")
        for cache_ref in node_refs.get("cache", [])[:2]:
            gen.add_edge(eks_ref, cache_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#C62828;strokeWidth=1;dashed=1;")

    # ECS -> Data
    for ecs_ref in node_refs.get("ecs", []):
        for rds_ref in node_refs.get("rds", [])[:2]:
            gen.add_edge(ecs_ref, rds_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7B1FA2;strokeWidth=1;dashed=1;")
        for cache_ref in node_refs.get("cache", [])[:2]:
            gen.add_edge(ecs_ref, cache_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#C62828;strokeWidth=1;dashed=1;")

    # Beanstalk -> Data
    for eb_ref in node_refs.get("beanstalk", []):
        for rds_ref in node_refs.get("rds", [])[:1]:
            gen.add_edge(eb_ref, rds_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7B1FA2;strokeWidth=1;dashed=1;")
        for cache_ref in node_refs.get("cache", [])[:1]:
            gen.add_edge(eb_ref, cache_ref, "", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#C62828;strokeWidth=1;dashed=1;")

    # Generate and write
    xml_content = gen.generate_xml(f"AWS Architecture - {vpc_name}")
    with open(f"{output_name}.drawio", "w") as f:
        f.write(xml_content)
    print(f"  Created: {output_name}.drawio")


def main():
    parser = argparse.ArgumentParser(description="Generate AWS architecture diagrams in draw.io format")
    parser.add_argument("--input", default="output/inventory.json")
    parser.add_argument("--output", default="output/architecture")
    parser.add_argument("--vpc", help="Generate diagram for specific VPC ID")
    parser.add_argument("--k8s-workloads", default="output/k8s_workloads.json")
    args = parser.parse_args()

    print(f"Loading inventory from {args.input}...")
    inventory = load_inventory(args.input)

    k8s_workloads = load_k8s_workloads(args.k8s_workloads)
    if k8s_workloads:
        print(f"Loaded K8s workloads for {len(k8s_workloads)} clusters")

    # Load CloudFront data (global)
    cloudfront_data = inventory.get("cloudfront", {})
    if cloudfront_data.get("distributions"):
        print(f"Loaded {len(cloudfront_data['distributions'])} CloudFront distributions")

    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    diagram_count = 0
    for region_name, region_data in inventory.get("regions", {}).items():
        if "error" in region_data:
            continue

        vpcs = region_data.get("vpcs", [])
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
            if not args.vpc and vpc.get("is_default"):
                continue

            vpc_name = get_resource_name(vpc, "vpc_id")
            safe_name = vpc_name.replace(" ", "_").replace("/", "_").replace("-", "_")
            output_file = f"{args.output}_{region_name}_{safe_name}"

            print(f"Generating draw.io diagram for VPC: {vpc_name} ({vpc['vpc_id']})...")

            generate_drawio_diagram(
                vpc, ec2_instances, ecs_clusters, eks_clusters,
                rds_data, elasticache_data, load_balancers, output_file,
                region_name, k8s_workloads, elasticbeanstalk_data, redshift_data,
                cloudfront_data
            )
            diagram_count += 1

    if diagram_count == 0 and args.vpc:
        print(f"Error: VPC {args.vpc} not found in inventory")
    else:
        print(f"\nDiagram generation complete! Generated {diagram_count} draw.io diagram(s).")


if __name__ == "__main__":
    main()
