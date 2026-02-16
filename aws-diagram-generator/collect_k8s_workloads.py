#!/usr/bin/env python3
"""
K8s Workloads Collector

Collects Kubernetes workloads (pods, deployments, services) from EKS clusters.
Requires kubeconfig contexts to be set up for EKS clusters.

Usage:
    python collect_k8s_workloads.py
    python collect_k8s_workloads.py --inventory output/inventory.json
    python collect_k8s_workloads.py --output output/k8s_workloads.json
"""

import argparse
import json
import os
from typing import Dict, Any, List

from collectors.k8s_collector import K8sCollector
from utils.logger import get_logger

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Collect K8s workloads from EKS clusters")
    parser.add_argument(
        "--inventory",
        default="output/inventory.json",
        help="Path to inventory JSON file"
    )
    parser.add_argument(
        "--output",
        default="output/k8s_workloads.json",
        help="Output file for K8s workloads"
    )
    parser.add_argument(
        "--clusters",
        nargs="+",
        help="Specific cluster names to collect (default: all from inventory)"
    )
    return parser.parse_args()


def load_inventory(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r") as f:
        return json.load(f)


def get_eks_clusters_from_inventory(inventory: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all EKS clusters from inventory."""
    clusters = []
    for region_name, region_data in inventory.get("regions", {}).items():
        if "error" in region_data:
            continue
        for cluster in region_data.get("eks_clusters", []):
            cluster["region"] = region_name
            clusters.append(cluster)
    return clusters


def main():
    args = parse_args()

    logger.info("=" * 60)
    logger.info("K8s Workloads Collector")
    logger.info("=" * 60)
    logger.info(f"Inventory: {args.inventory}")
    logger.info(f"Output: {args.output}")
    logger.info("=" * 60)

    # Load inventory
    try:
        inventory = load_inventory(args.inventory)
        logger.info(f"Loaded inventory from {args.inventory}")
    except FileNotFoundError:
        logger.error(f"Inventory file not found: {args.inventory}")
        logger.error("Run main.py first to generate inventory")
        return

    # Get EKS clusters
    eks_clusters = get_eks_clusters_from_inventory(inventory)
    logger.info(f"Found {len(eks_clusters)} EKS clusters in inventory")

    # Filter if specific clusters requested
    if args.clusters:
        eks_clusters = [c for c in eks_clusters if c.get("cluster_name") in args.clusters]
        logger.info(f"Filtered to {len(eks_clusters)} clusters: {args.clusters}")

    if not eks_clusters:
        logger.warning("No EKS clusters found")
        return

    # Collect workloads
    collector = K8sCollector()
    all_workloads = {}

    for cluster in eks_clusters:
        cluster_name = cluster.get("cluster_name", "unknown")
        region = cluster.get("region", "unknown")
        logger.info(f"\nCollecting from cluster: {cluster_name} ({region})")

        try:
            workloads = collector.collect_cluster_workloads(cluster)
            workloads["region"] = region

            if workloads.get("error"):
                logger.warning(f"  Error: {workloads['error']}")
            else:
                logger.info(f"  Namespaces: {len(workloads.get('namespaces', []))}")
                logger.info(f"  Deployments: {len(workloads.get('deployments', []))}")
                logger.info(f"  Pods: {len(workloads.get('pods', []))}")
                logger.info(f"  Services: {len(workloads.get('services', []))}")
                logger.info(f"  Nodes with pods: {len(workloads.get('pods_by_node', {}))}")

            all_workloads[cluster_name] = workloads

        except Exception as e:
            logger.error(f"  Failed to collect from {cluster_name}: {e}")
            all_workloads[cluster_name] = {
                "cluster_name": cluster_name,
                "region": region,
                "error": str(e)
            }

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write output
    with open(args.output, "w") as f:
        json.dump(all_workloads, f, indent=2, default=str)

    logger.info("=" * 60)
    logger.info(f"K8s workloads saved to: {args.output}")
    logger.info("=" * 60)

    # Summary
    print("\n" + "=" * 60)
    print("K8S WORKLOADS SUMMARY")
    print("=" * 60)

    for cluster_name, data in all_workloads.items():
        if data.get("error"):
            print(f"\n{cluster_name}: ERROR - {data['error']}")
        else:
            print(f"\n{cluster_name}:")
            print(f"  Namespaces: {len(data.get('namespaces', []))}")
            print(f"  Deployments: {len(data.get('deployments', []))}")
            print(f"  Pods: {len(data.get('pods', []))}")
            print(f"  Services: {len(data.get('services', []))}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
