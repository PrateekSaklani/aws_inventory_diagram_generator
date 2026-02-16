#!/usr/bin/env python3
"""
Setup EKS Access Entry for inventory reader role.

This script adds read-only Kubernetes access for the specified IAM role
using EKS Access Entries (does not modify aws-auth ConfigMap).

Usage:
    python setup_eks_access.py --cluster dev-baraka-a74cd860 --role-arn arn:aws:iam::653404384870:role/Organization-Read-Role
    python setup_eks_access.py --cluster dev-baraka-a74cd860 --role-arn arn:aws:iam::653404384870:role/Organization-Read-Role --remove
"""

import argparse
import boto3
from botocore.exceptions import ClientError


def create_access_entry(eks_client, cluster_name: str, role_arn: str):
    """Create EKS access entry for the IAM role."""
    print(f"Creating access entry for {role_arn}...")

    try:
        response = eks_client.create_access_entry(
            clusterName=cluster_name,
            principalArn=role_arn,
            type='STANDARD'
        )
        print(f"  Access entry created")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"  Access entry already exists")
            return True
        else:
            print(f"  Error: {e.response['Error']['Message']}")
            return False


def associate_access_policy(eks_client, cluster_name: str, role_arn: str):
    """Associate AmazonEKSViewPolicy with the access entry."""
    print(f"Associating AmazonEKSViewPolicy (read-only)...")

    try:
        response = eks_client.associate_access_policy(
            clusterName=cluster_name,
            principalArn=role_arn,
            policyArn='arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy',
            accessScope={
                'type': 'cluster'
            }
        )
        print(f"  Policy associated")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"  Policy already associated")
            return True
        else:
            print(f"  Error: {e.response['Error']['Message']}")
            return False


def delete_access_entry(eks_client, cluster_name: str, role_arn: str):
    """Remove EKS access entry for the IAM role."""
    print(f"Removing access entry for {role_arn}...")

    try:
        response = eks_client.delete_access_entry(
            clusterName=cluster_name,
            principalArn=role_arn
        )
        print(f"  Access entry removed")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  Access entry does not exist")
            return True
        else:
            print(f"  Error: {e.response['Error']['Message']}")
            return False


def list_access_entries(eks_client, cluster_name: str):
    """List all access entries for the cluster."""
    print(f"\nCurrent access entries for {cluster_name}:")

    try:
        response = eks_client.list_access_entries(clusterName=cluster_name)
        entries = response.get('accessEntries', [])

        if not entries:
            print("  (none)")
            return

        for arn in entries:
            try:
                details = eks_client.describe_access_entry(
                    clusterName=cluster_name,
                    principalArn=arn
                )
                entry = details.get('accessEntry', {})
                entry_type = entry.get('type', 'N/A')

                policies = eks_client.list_associated_access_policies(
                    clusterName=cluster_name,
                    principalArn=arn
                )
                policy_names = [p.get('policyArn', '').split('/')[-1] for p in policies.get('associatedAccessPolicies', [])]

                print(f"  - {arn}")
                print(f"    Type: {entry_type}, Policies: {', '.join(policy_names) or 'none'}")
            except:
                print(f"  - {arn}")

    except ClientError as e:
        print(f"  Error: {e.response['Error']['Message']}")


def get_assumed_role_session(role_arn: str, region: str):
    """Assume IAM role and return boto3 session."""
    sts = boto3.client('sts', region_name=region)
    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName='EKSAccessSetup',
        DurationSeconds=3600
    )
    credentials = response['Credentials']
    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name=region
    )


def main():
    parser = argparse.ArgumentParser(description="Setup EKS Access Entry for inventory reader")
    parser.add_argument("--cluster", required=True, help="EKS cluster name")
    parser.add_argument("--role-arn", required=True, help="IAM role ARN to grant access")
    parser.add_argument("--region", default="me-south-1", help="AWS region")
    parser.add_argument("--remove", action="store_true", help="Remove access instead of adding")
    parser.add_argument("--list-only", action="store_true", help="Only list existing access entries")
    parser.add_argument("--assume-role", help="Assume this role to run the setup (for cross-account)")
    args = parser.parse_args()

    if args.assume_role:
        print(f"Assuming role: {args.assume_role}")
        session = get_assumed_role_session(args.assume_role, args.region)
        eks_client = session.client('eks')
    else:
        eks_client = boto3.client('eks', region_name=args.region)

    print("=" * 60)
    print("EKS Access Entry Setup")
    print("=" * 60)
    print(f"Cluster: {args.cluster}")
    print(f"Role ARN: {args.role_arn}")
    print(f"Region: {args.region}")
    print(f"Action: {'REMOVE' if args.remove else 'LIST ONLY' if args.list_only else 'ADD'}")
    print("=" * 60)

    if args.list_only:
        list_access_entries(eks_client, args.cluster)
        return

    if args.remove:
        delete_access_entry(eks_client, args.cluster, args.role_arn)
    else:
        if create_access_entry(eks_client, args.cluster, args.role_arn):
            associate_access_policy(eks_client, args.cluster, args.role_arn)

    list_access_entries(eks_client, args.cluster)
    print("\nDone!")


if __name__ == "__main__":
    main()
