# Terraform configuration for DTO infrastructure
# This is an example configuration - adapt for your cloud provider

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

# Variables
variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "dto-cluster"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "dto_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.cluster_name}-vpc"
    Environment = var.environment
    Project     = "dto"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "dto_igw" {
  vpc_id = aws_vpc.dto_vpc.id

  tags = {
    Name        = "${var.cluster_name}-igw"
    Environment = var.environment
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.dto_vpc.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.cluster_name}-public-${count.index + 1}"
    Environment = var.environment
    Type        = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.dto_vpc.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "${var.cluster_name}-private-${count.index + 1}"
    Environment = var.environment
    Type        = "private"
  }
}

# NAT Gateways
resource "aws_eip" "nat" {
  count = 2

  domain = "vpc"
  
  tags = {
    Name        = "${var.cluster_name}-nat-eip-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_nat_gateway" "dto_nat" {
  count = 2

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "${var.cluster_name}-nat-${count.index + 1}"
    Environment = var.environment
  }

  depends_on = [aws_internet_gateway.dto_igw]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.dto_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.dto_igw.id
  }

  tags = {
    Name        = "${var.cluster_name}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table" "private" {
  count = 2

  vpc_id = aws_vpc.dto_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.dto_nat[count.index].id
  }

  tags = {
    Name        = "${var.cluster_name}-private-rt-${count.index + 1}"
    Environment = var.environment
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "dto_cluster_sg" {
  name_prefix = "${var.cluster_name}-cluster-sg"
  vpc_id      = aws_vpc.dto_vpc.id

  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-cluster-sg"
    Environment = var.environment
  }
}

# S3 Bucket for Artifacts
resource "aws_s3_bucket" "dto_artifacts" {
  bucket = "${var.cluster_name}-artifacts-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.cluster_name}-artifacts"
    Environment = var.environment
    Purpose     = "dto-artifacts"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "dto_artifacts" {
  bucket = aws_s3_bucket.dto_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "dto_artifacts" {
  bucket = aws_s3_bucket.dto_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "dto_artifacts" {
  bucket = aws_s3_bucket.dto_artifacts.id

  rule {
    id     = "artifact_lifecycle"
    status = "Enabled"

    expiration {
      days = 30  # Match BRD artifact retention policy
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

# RDS Instance for PostgreSQL
resource "aws_db_subnet_group" "dto_db" {
  name       = "${var.cluster_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name        = "${var.cluster_name}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "dto_db_sg" {
  name_prefix = "${var.cluster_name}-db-sg"
  vpc_id      = aws_vpc.dto_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.dto_cluster_sg.id]
  }

  tags = {
    Name        = "${var.cluster_name}-db-sg"
    Environment = var.environment
  }
}

resource "aws_db_instance" "dto_db" {
  identifier = "${var.cluster_name}-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"  # Adjust for production

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true

  db_name  = "dto"
  username = "dto"
  password = random_password.db_password.result

  vpc_security_group_ids = [aws_security_group.dto_db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.dto_db.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = true  # Set to false for production

  tags = {
    Name        = "${var.cluster_name}-db"
    Environment = var.environment
  }
}

resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Secrets Manager for database password
resource "aws_secretsmanager_secret" "dto_db_password" {
  name = "${var.cluster_name}-db-password"

  tags = {
    Name        = "${var.cluster_name}-db-password"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "dto_db_password" {
  secret_id = aws_secretsmanager_secret.dto_db_password.id
  secret_string = jsonencode({
    username = aws_db_instance.dto_db.username
    password = random_password.db_password.result
    host     = aws_db_instance.dto_db.endpoint
    port     = aws_db_instance.dto_db.port
    dbname   = aws_db_instance.dto_db.db_name
  })
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.dto_vpc.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.dto_db.endpoint
  sensitive   = true
}

output "artifacts_bucket" {
  description = "S3 bucket for artifacts"
  value       = aws_s3_bucket.dto_artifacts.bucket
}

output "database_secret_arn" {
  description = "ARN of the database secret in Secrets Manager"
  value       = aws_secretsmanager_secret.dto_db_password.arn
}
