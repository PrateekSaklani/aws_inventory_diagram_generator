# AWS Architecture Inventory & Diagram Generator

A comprehensive Python tool that automatically discovers and inventories AWS resources across multiple regions and generates visual architecture diagrams in multiple formats (Draw.io, PNG).

## Features

- **Multi-region Discovery** - Scan AWS resources across specified regions
- **Cross-account Access** - Support for IAM role assumption
- **Comprehensive Resource Collection** - VPC, EC2, ECS, EKS, RDS, ElastiCache, Load Balancers, CloudFront, Redshift, and more
- **Kubernetes Workload Discovery** - Collect pods, deployments, and services from EKS clusters
- **Multiple Output Formats** - JSON inventory, Draw.io XML diagrams, and PNG images
- **Structured Data Models** - Type-safe data models for all AWS resources
- **Relationship Mapping** - Track connections between resources (subnets, security groups, target groups)

## Supported AWS Services

| Category | Services |
|----------|----------|
| Compute | EC2, ECS, EKS, Fargate, Elastic Beanstalk |
| Database | RDS, Aurora, ElastiCache (Redis/Memcached), Redshift |
| Networking | VPC, Subnets, Internet Gateway, NAT Gateway, Route Tables, Security Groups, VPC Endpoints |
| Load Balancing | ALB, NLB, CLB, Target Groups |
| Content Delivery | CloudFront Distributions |
| Kubernetes | EKS Clusters, Node Groups, Pods, Deployments, Services |

## Installation

### Prerequisites

- Python 3.8+
- AWS credentials configured (via AWS CLI, environment variables, or IAM role)
- `kubectl` configured (for Kubernetes workload collection)

### Setup

```bash
# Clone the repository
cd aws-diagram-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Edit `config.py` to customize:

```python
# AWS regions to scan
REGIONS = ["us-east-1", "eu-west-1"]

# AWS profile (optional)
AWS_PROFILE = "default"

# IAM role for cross-account access (optional)
ROLE_ARN = None  # or "arn:aws:iam::123456789012:role/ReadOnlyRole"

# Services to collect
COLLECT_VPC = True
COLLECT_EC2 = True
COLLECT_ECS = True
COLLECT_EKS = True
COLLECT_RDS = True
COLLECT_REDIS = True
COLLECT_ELB = True
COLLECT_CLOUDFRONT = True
COLLECT_REDSHIFT = True
COLLECT_ELASTICBEANSTALK = True

# Output configuration
OUTPUT_FILE = "output/inventory.json"
```

## Usage

### 1. Collect AWS Inventory

```bash
python main.py
```

This generates `output/inventory.json` containing all discovered AWS resources.

**CLI Options:**
```bash
python main.py --regions us-east-1 eu-west-1 --profile myprofile --output my_inventory.json
```

### 2. Collect Kubernetes Workloads (Optional)

```bash
python collect_k8s_workloads.py
```

This reads EKS clusters from the inventory and collects Kubernetes workloads, outputting to `output/k8s_workloads.json`.

### 3. Generate Diagrams

**Basic Diagram:**
```bash
python diagram_generator.py
```

**Detailed Diagram (with ECS services, EKS node groups):**
```bash
python diagram_generator_detailed.py
```

**Draw.io Diagram:**
```bash
python diagram_generator_drawio.py
```

## Project Structure

```
aws-diagram-generator/
├── main.py                          # Main inventory collection script
├── config.py                        # Configuration settings
├── diagram_generator.py             # Basic diagram generation
├── diagram_generator_detailed.py    # Detailed PNG diagrams
├── diagram_generator_drawio.py      # Draw.io XML generation
├── collect_k8s_workloads.py         # K8s workload collection
├── requirements.txt                 # Python dependencies
│
├── collectors/                      # AWS resource collectors
│   ├── vpc_collector.py
│   ├── ecs_collector.py
│   ├── eks_collector.py
│   ├── rds_collector.py
│   ├── redis_collector.py
│   ├── elb_collector.py
│   ├── elasticbeanstalk_collector.py
│   ├── redshift_collector.py
│   ├── cloudfront_collector.py
│   └── k8s_collector.py
│
├── aws_clients/                     # AWS API wrapper clients
│   ├── ec2.py
│   ├── ecs.py
│   ├── eks.py
│   ├── rds.py
│   ├── elasticache.py
│   ├── elb.py
│   ├── elasticbeanstalk.py
│   ├── redshift.py
│   └── cloudfront.py
│
├── models/                          # Data models for AWS resources
│   ├── vpc.py
│   ├── rds.py
│   ├── eks.py
│   ├── ecs.py
│   ├── redis.py
│   ├── elasticbeanstalk.py
│   └── redshift.py
│
├── utils/                           # Utility modules
│   ├── aws_session.py              # AWS session management
│   └── logger.py                   # Logging configuration
│
└── output/                          # Generated output files
    ├── inventory.json              # AWS resource inventory
    ├── k8s_workloads.json          # Kubernetes workloads
    └── *.drawio                    # Draw.io diagram files
```

## Output Examples

### Inventory JSON Structure

```json
{
  "regions": {
    "us-east-1": {
      "vpcs": [...],
      "subnets": [...],
      "ec2_instances": [...],
      "ecs_clusters": [...],
      "eks_clusters": [...],
      "rds_instances": [...],
      "load_balancers": [...]
    }
  },
  "global": {
    "cloudfront_distributions": [...]
  }
}
```

### Draw.io Diagrams

Generated Draw.io files include:
- VPC boundaries with subnet layouts
- Resource icons with AWS styling
- Connection lines showing relationships
- Availability zone organization

## Requirements

- `boto3>=1.34.0` - AWS SDK for Python
- `botocore>=1.34.0` - AWS API interaction
- `kubernetes` - Kubernetes API client
- `diagrams` - Diagram generation library (for PNG output)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
