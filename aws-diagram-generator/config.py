"""
AWS Inventory Configuration
"""

# AWS Regions to scan
REGIONS = [
    "me-south-1"
]

# AWS Profile (None uses default credentials)
AWS_PROFILE = "prod"

# IAM Role to assume (optional)
# Set ROLE_ARN to assume a specific role for cross-account access
# Leave as None to use default credentials
ROLE_ARN = None

# External ID for role assumption (optional, required by some roles)
EXTERNAL_ID = None

# Session name for assumed role
ROLE_SESSION_NAME = "AWSInventoryGenerator"

# Output settings
OUTPUT_FILE = "output/inventory.json"

# Services to collect (set to False to skip)
COLLECT_SERVICES = {
    "vpc": True,
    "ec2": True,
    "ecs": True,
    "eks": True,
    "rds": True,
    "elasticache": True,
    "elb": True,
    "elasticbeanstalk": True,
    "redshift": True,
}

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
