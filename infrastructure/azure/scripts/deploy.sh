#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
echo "🚀 Deploying Mew Assistant to Azure - Environment: $ENVIRONMENT"

cd infrastructure/azure/terraform
terraform init
terraform plan -var="environment=$ENVIRONMENT"
terraform apply -var="environment=$ENVIRONMENT" -auto-approve

echo "✅ Deployment complete!"
terraform output
