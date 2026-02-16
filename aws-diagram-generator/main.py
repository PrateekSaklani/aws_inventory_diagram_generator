#!/usr/bin/env python3
"""
AWS Inventory Generator

Fetches all AWS resources from specified regions using read-only access
and generates an inventory.json file.

Usage:
    python main.py
    python main.py --regions us-east-1 us-west-2
    python main.py --profile my-aws-profile
    python main.py --output custom-inventory.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

import config
from utils.aws_session import AWSSession
from utils.logger import get_logger
from collectors.vpc_collector import VPCCollector
from collectors.ecs_collector import ECSCollector
from collectors.eks_collector import EKSCollector
from collectors.rds_collector import RDSCollector
from collectors.redis_collector import RedisCollector
from collectors.elb_collector import ELBCollector
from collectors.elasticbeanstalk_collector import ElasticBeanstalkCollector
from collectors.redshift_collector import RedshiftCollector
from collectors.cloudfront_collector import CloudFrontCollector

logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch AWS resources and generate inventory"
    )
    parser.add_argument(
        "--regions",
        nargs="+",
        default=config.REGIONS,
        help="AWS regions to scan (default: from config.py)"
    )
    parser.add_argument(
        "--profile",
        default=config.AWS_PROFILE,
        help="AWS profile to use (default: from config.py or default credentials)"
    )
    parser.add_argument(
        "--output",
        default=config.OUTPUT_FILE,
        help="Output file path (default: output/inventory.json)"
    )
    parser.add_argument(
        "--services",
        nargs="+",
        choices=["vpc", "ec2", "ecs", "eks", "rds", "elasticache", "elb", "elasticbeanstalk", "redshift", "cloudfront", "all"],
        default=["all"],
        help="Services to collect (default: all)"
    )
    parser.add_argument(
        "--role-arn",
        default=config.ROLE_ARN,
        help="IAM role ARN to assume (default: from config.py)"
    )
    parser.add_argument(
        "--external-id",
        default=config.EXTERNAL_ID,
        help="External ID for role assumption (default: from config.py)"
    )
    return parser.parse_args()


def collect_region_resources(
    session: AWSSession,
    region: str,
    services: List[str]
) -> Dict[str, Any]:
    """Collect all resources for a single region."""
    logger.info(f"Starting collection for region: {region}")

    region_data = {
        "region": region,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }

    collect_all = "all" in services

    # VPC and EC2
    if collect_all or "vpc" in services or "ec2" in services:
        try:
            vpc_collector = VPCCollector(session, region)
            vpcs = vpc_collector.collect()
            region_data["vpcs"] = [vpc.to_dict() for vpc in vpcs]

            if collect_all or "ec2" in services:
                region_data["ec2_instances"] = vpc_collector.collect_ec2_instances()
        except Exception as e:
            logger.error(f"Error collecting VPC/EC2 in {region}: {e}")
            region_data["vpcs"] = []
            region_data["ec2_instances"] = []

    # ECS
    if collect_all or "ecs" in services:
        try:
            ecs_collector = ECSCollector(session, region)
            clusters = ecs_collector.collect()
            region_data["ecs_clusters"] = [c.to_dict() for c in clusters]
        except Exception as e:
            logger.error(f"Error collecting ECS in {region}: {e}")
            region_data["ecs_clusters"] = []

    # EKS
    if collect_all or "eks" in services:
        try:
            eks_collector = EKSCollector(session, region)
            clusters = eks_collector.collect()
            region_data["eks_clusters"] = [c.to_dict() for c in clusters]
        except Exception as e:
            logger.error(f"Error collecting EKS in {region}: {e}")
            region_data["eks_clusters"] = []

    # RDS
    if collect_all or "rds" in services:
        try:
            rds_collector = RDSCollector(session, region)
            region_data["rds"] = rds_collector.collect()
        except Exception as e:
            logger.error(f"Error collecting RDS in {region}: {e}")
            region_data["rds"] = {"instances": [], "clusters": []}

    # ElastiCache (Redis/Memcached)
    if collect_all or "elasticache" in services:
        try:
            redis_collector = RedisCollector(session, region)
            region_data["elasticache"] = redis_collector.collect()
        except Exception as e:
            logger.error(f"Error collecting ElastiCache in {region}: {e}")
            region_data["elasticache"] = {
                "clusters": [],
                "replication_groups": [],
                "serverless_caches": []
            }

    # ELB
    if collect_all or "elb" in services:
        try:
            elb_collector = ELBCollector(session, region)
            region_data["load_balancers"] = elb_collector.collect()
        except Exception as e:
            logger.error(f"Error collecting ELB in {region}: {e}")
            region_data["load_balancers"] = {
                "application_load_balancers": [],
                "network_load_balancers": [],
                "classic_load_balancers": [],
                "target_groups": []
            }

    # Elastic Beanstalk
    if collect_all or "elasticbeanstalk" in services:
        try:
            eb_collector = ElasticBeanstalkCollector(session, region)
            region_data["elasticbeanstalk"] = eb_collector.collect()
        except Exception as e:
            logger.error(f"Error collecting Elastic Beanstalk in {region}: {e}")
            region_data["elasticbeanstalk"] = {
                "applications": [],
                "environments": []
            }

    # Redshift
    if collect_all or "redshift" in services:
        try:
            redshift_collector = RedshiftCollector(session, region)
            region_data["redshift"] = redshift_collector.collect()
        except Exception as e:
            logger.error(f"Error collecting Redshift in {region}: {e}")
            region_data["redshift"] = {
                "clusters": [],
                "serverless_workgroups": [],
                "serverless_namespaces": []
            }

    logger.info(f"Completed collection for region: {region}")
    return region_data


def main():
    """Main entry point."""
    args = parse_args()

    logger.info("=" * 60)
    logger.info("AWS Inventory Generator")
    logger.info("=" * 60)
    logger.info(f"Regions: {args.regions}")
    logger.info(f"Profile: {args.profile or 'default credentials'}")
    logger.info(f"Role ARN: {args.role_arn or 'None (using direct credentials)'}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Services: {args.services}")
    logger.info("=" * 60)

    # Create session
    session = AWSSession(
        profile=args.profile,
        role_arn=args.role_arn,
        external_id=args.external_id
    )

    # Get account info
    try:
        account_id = session.get_account_id()
        logger.info(f"AWS Account ID: {account_id}")
    except Exception as e:
        logger.error(f"Failed to get AWS account info: {e}")
        logger.error("Please check your AWS credentials and permissions.")
        sys.exit(1)

    # Initialize inventory
    inventory = {
        "metadata": {
            "account_id": account_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "regions_scanned": args.regions,
            "services_collected": args.services,
            "role_arn": args.role_arn,
        },
        "regions": {}
    }

    # Collect resources from each region
    for region in args.regions:
        try:
            region_session = AWSSession(
                profile=args.profile,
                region=region,
                role_arn=args.role_arn,
                external_id=args.external_id
            )
            region_data = collect_region_resources(
                region_session,
                region,
                args.services
            )
            inventory["regions"][region] = region_data
        except Exception as e:
            logger.error(f"Failed to collect resources from {region}: {e}")
            inventory["regions"][region] = {
                "region": region,
                "error": str(e)
            }

    # Collect global services (CloudFront)
    collect_all = "all" in args.services
    if collect_all or "cloudfront" in args.services:
        try:
            # CloudFront is global, use us-east-1
            global_session = AWSSession(
                profile=args.profile,
                region="us-east-1",
                role_arn=args.role_arn,
                external_id=args.external_id
            )
            cf_collector = CloudFrontCollector(global_session)
            inventory["cloudfront"] = cf_collector.collect()
        except Exception as e:
            logger.error(f"Failed to collect CloudFront: {e}")
            inventory["cloudfront"] = {"distributions": []}

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write inventory to file
    with open(args.output, "w") as f:
        json.dump(inventory, f, indent=2, default=str)

    logger.info("=" * 60)
    logger.info(f"Inventory saved to: {args.output}")
    logger.info("=" * 60)

    # Print summary
    print("\n" + "=" * 60)
    print("INVENTORY SUMMARY")
    print("=" * 60)

    for region, data in inventory["regions"].items():
        if "error" in data:
            print(f"\n{region}: ERROR - {data['error']}")
            continue

        print(f"\n{region}:")
        if "vpcs" in data:
            print(f"  VPCs: {len(data.get('vpcs', []))}")
        if "ec2_instances" in data:
            print(f"  EC2 Instances: {len(data.get('ec2_instances', []))}")
        if "ecs_clusters" in data:
            print(f"  ECS Clusters: {len(data.get('ecs_clusters', []))}")
        if "eks_clusters" in data:
            print(f"  EKS Clusters: {len(data.get('eks_clusters', []))}")
        if "rds" in data:
            rds = data.get("rds", {})
            print(f"  RDS Instances: {len(rds.get('instances', []))}")
            print(f"  RDS Clusters: {len(rds.get('clusters', []))}")
        if "elasticache" in data:
            ec = data.get("elasticache", {})
            print(f"  ElastiCache Clusters: {len(ec.get('clusters', []))}")
            print(f"  Replication Groups: {len(ec.get('replication_groups', []))}")
        if "load_balancers" in data:
            lb = data.get("load_balancers", {})
            print(f"  ALBs: {len(lb.get('application_load_balancers', []))}")
            print(f"  NLBs: {len(lb.get('network_load_balancers', []))}")
            print(f"  CLBs: {len(lb.get('classic_load_balancers', []))}")
        if "elasticbeanstalk" in data:
            eb = data.get("elasticbeanstalk", {})
            print(f"  Beanstalk Apps: {len(eb.get('applications', []))}")
            print(f"  Beanstalk Envs: {len(eb.get('environments', []))}")
        if "redshift" in data:
            rs = data.get("redshift", {})
            print(f"  Redshift Clusters: {len(rs.get('clusters', []))}")
            print(f"  Redshift Serverless: {len(rs.get('serverless_workgroups', []))}")

    # CloudFront (global)
    if "cloudfront" in inventory:
        cf = inventory.get("cloudfront", {})
        print(f"\nGlobal Services:")
        print(f"  CloudFront Distributions: {len(cf.get('distributions', []))}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
