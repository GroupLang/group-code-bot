#!/bin/bash
set -e

# Define required variables
AWS_ACCOUNT_ID="110353082702"  # Tu ID de cuenta AWS
AWS_REGION="us-east-1"  # Región de AWS
ECR_REPOSITORY_NAME="github-repo"

# Build the Docker image
docker build -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:latest .

# Authenticate with AWS ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Push the image to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:latest

# Navigate to the infrastructure directory
cd infrastructure

# Deploy using Terraform
terraform init
terraform apply -auto-approve
